# Phantom Engine - Writeup

## Analysis

### The Dispatcher
there is a `dispatch` function which selects between a decoy and a real validation function. The selection logic `(input[4] * input[7]) & 1` determines the path.
- **Goal**: Reach `validate`.

### The Validation Logic
The real validation logic checks `input[i] ^ key(i, seed) == data[i]`.
- **Seed**: Derived from `input[0] ^ input[LEN-1]`.
- **Blob**: A packed `u64` array that gets unpacked into bytes.

### The Problem (Bug?)
The binary as-is has subtle bugs (integer overflows) that might cause it to crash or behave incorrectly. However, a static analysis reveals the intent:
- It's a key-based XOR check.
- The `seed` is a single byte (0-255).

## Solution

1. **Extract the Blob**: Copy the `blob` array and the `unpack` logic to get the target bytes.
2. **Brute Force the Seed**: Since the seed is only 1 byte (256 possibilities), we can bruteforce it.
   - For each seed `s` in `0..255`:
     - Calculate potential flag: `candidate[i] = blob[i] ^ key(i, s)`
     - Check the result. If it looks like `bpctf{...}`, we win.
3. **The Correct Seed**: It turns out the correct seed is `31`.
4. **Decrypt**:
   - Using seed 31, the key generation logic produces a sequence of keys.
   - XORing these keys with the blob yields: `bpctf{phantom_runtime_engine}`.

> [!WARNING]
> *The challenge binary might crash if you run it blindly due to Zig's safety checks (integer overflow). This forces the solver to statically analyze the logic or fix the binary to run it.*
