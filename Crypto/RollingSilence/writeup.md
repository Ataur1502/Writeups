<div align="center">

# ChallengeCrypto2 — Rolling Silence

**Category:** **Cryptography** + Reverse Engineering
**Language:** x86_64 Assembly
**Difficulty:** Easy-Medium
**Author:** ZenRage

</div>

---

## Overview

In this challenge, we are given a **stripped x86_64 ELF binary** with:

* No input
* No output
* No visible strings
* No plaintext stored in memory

The flag is decrypted **entirely in registers** using a rolling XOR cipher and is never written to memory or printed.

The goal is to **recover the flag** by analyzing the binary and reconstructing the cryptographic logic.

---

## Step 1 — Initial Reconnaissance

Run the binary:

```bash
./rollingsilence
```

Result:

* No output
* Clean exit

Check file type:

```bash
file rollingsilence
```

```
ELF 64-bit LSB executable, x86-64, statically linked, stripped
```

This suggests:

* No symbols
* Static analysis required
* Likely internal computation only

---

## Step 2 — Locate Encrypted Data

Inspect the `.rodata` section:

```bash
objdump -s -j .rodata rollingsilence
```

Output:

```
402000 ebc6a948 bd61e983 19c1b570 de58b849
402010 8e2816f1 55a5092d 2062
```

These are **high-entropy bytes**, strongly indicating **ciphertext**.

---

## Step 3 — Extract Ciphertext

Convert the hex bytes into decimal values:

```python
hex_bytes = """
eb c6 a9 48 bd 61 e9 83 19 c1
b5 70 de 58 b8 49 8e 28 16 f1
55 a5 09 2d 20 62
"""

ciphertext = [int(b, 16) for b in hex_bytes.split()]
print(ciphertext, len(ciphertext))
```

Result:

```text
[235, 198, 169, 72, 189, 97, 233, 131, 25, 193,
 181, 112, 222, 88, 184, 73, 142, 40, 22, 241,
 85, 165, 9, 45, 32, 98]
26
```

---

## Step 4 — Disassemble the Binary

Disassemble the `.text` section:

```bash
objdump -d rollingsilence
```

Key loop:

```asm
xor    rdi, rdi          ; index = 0
mov    al, 0x89          ; initial key
cmp    rdi, 0x1a         ; loop length = 26
jge    exit

mov    bl, [ciphertext + rdi]
xor    bl, al            ; decrypt byte

add    al, dil
rol    al, 1
xor    al, 0xa5          ; key evolution

inc    rdi
jmp    loop
```

---

## Step 5 — Identify the Cryptographic Primitive

From the disassembly:

* `bl = ciphertext[i] ^ key`
* `al` holds the **rolling key**
* The key evolves every iteration

This is a **rolling XOR stream cipher**.

### Mathematical form:

```
K₀ = 0x89

P[i] = C[i] ⊕ K[i]

K[i+1] = rol((K[i] + i) mod 256, 1) ⊕ 0xA5
```

---

## Step 6 — (Optional) Dynamic Verification in GDB

Set a breakpoint **after** the XOR instruction:

```gdb
break *0x401013
run
```

Inspect registers:

```gdb
p/c $bl
```

You will see:

```
'b'
'p'
'c'
't'
'f'
'{'
...
```

To automatically dump the full flag:

```gdb
commands 1
silent
printf "%c", $bl
continue
end
run
```

Output:

```
bpctf{registers_are_state}
```

---

## Step 7 — Intended Solution (Offline Decryption)

The correct solver approach is to **rebuild the cipher externally**, without debugging.

### Solver Script

```python
def rol8(x, r):
    return ((x << r) | (x >> (8 - r))) & 0xff


ciphertext = [
    235, 198, 169, 72, 189, 97, 233, 131, 25, 193,
    181, 112, 222, 88, 184, 73, 142, 40, 22, 241,
    85, 165, 9, 45, 32, 98
]

key = 0x89
plaintext = []

for i, c in enumerate(ciphertext):
    plaintext.append(c ^ key)
    key = (key + i) & 0xff
    key = rol8(key, 1)
    key ^= 0xA5

print(bytes(plaintext).decode())
```

### Output

```
bpctf{registers_are_state}
```

---

## Final Notes

* The flag is **never stored in memory**
* The cipher state exists **only in registers**
* Reverse engineering is used only to **recover the cryptographic algorithm**
* The actual solution is **pure cryptanalysis**

This challenge demonstrates that:

> **Execution state is cryptographic state.**

---

## Final Flag

```
bpctf{registers_are_state}
```
