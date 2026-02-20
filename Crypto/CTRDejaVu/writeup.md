<div align="center">

# ChallengeCrypto3 — CTR Déjà Vu

**Category:** Cryptography
**Difficulty:** Medium–Hard
**Flag format:** `bpctf{...}`
**Author:** Zenith

</div>

---

## Challenge Summary

The challenge provides two ciphertexts encrypted under the same unknown key using a stream-cipher-like construction. No nonce, IV, or key material is provided.

The objective is to recover the original plaintext (the flag).

The vulnerability lies in keystream reuse under a CTR-based encryption scheme.

---

## Given Files

```
challenge.txt
```

Contents:

```
ciphertext_1
ciphertext_2
```

No additional metadata is provided.

---

## Understanding the Encryption Model

CTR mode encryption follows:

```
C = P ⊕ KS
```

Where:

* `P` = plaintext
* `KS` = keystream generated from `(key, nonce, counter)`

For AES-CTR or AES-GCM:

```
KS_i = AES(key, nonce || counter_i)
```

If the **same nonce is reused with the same key**, then:

```
KS (ciphertext_1) = KS (ciphertext_2)
```

This results in catastrophic keystream reuse.

---

## Step 1 — Hypothesis: Keystream Reuse

Assume:

```
C1 = P1 ⊕ KS
C2 = P2 ⊕ KS
```

Then:

```
C1 ⊕ C2
= (P1 ⊕ KS) ⊕ (P2 ⊕ KS)
= P1 ⊕ P2
```

The keystream cancels out.

This is equivalent to the classical **two-time pad failure**.

---

## Step 2 — Testing the Hypothesis

Using CyberChef:

1. Apply **From Hex** to both ciphertexts.
2. XOR `ciphertext_1` with `ciphertext_2`.

The output is not random noise.

Instead, it contains structured printable ASCII.

This confirms:

```
ciphertext_1 ⊕ ciphertext_2 = plaintext_1 ⊕ plaintext_2
```

Keystream reuse is verified.

---

## Step 3 — Leveraging Known Plaintext Structure

CTF flags typically follow:

```
bpctf{...}
```

Thus, we can perform a known-plaintext attack.

We now possess:

```
X = P1 ⊕ P2
```

If we guess part of one plaintext, we can recover the corresponding part of the other.

---

## Step 4 — Crib Dragging

Given:

```
X = P1 ⊕ P2
```

Then:

```
P2 = X ⊕ guess_for_P1
```

Procedure:

1. Take XOR output (P1 ⊕ P2).
2. XOR with guessed plaintext prefix `bpctf{`.

If the guess is correct, the output becomes readable ASCII.

---

## Step 5 — Practical Execution

In CyberChef:

* Input: XOR result
* Apply XOR with:

```
bpctf{aes-
```

Output:

```
gcm-crypto}
```

This is valid ASCII and consistent with flag structure.

---

## Step 6 — Recover the Full Flag

Combining both plaintext segments:

```
bpctf{aes-gcm-crypto}
```

---

## Why This Works

CTR mode is a stream cipher construction.

Reusing a nonce results in:

* Identical keystream generation
* Plaintext XOR leakage
* Total loss of confidentiality

AES-GCM internally uses CTR for encryption.
Nonce reuse in GCM is therefore equally catastrophic for confidentiality.

This attack does **not** break AES.
It exploits misuse of the encryption mode.

---

## Security Implications

Nonce reuse in CTR-based encryption causes:

* Plaintext recovery
* Message linking
* Potential forgery attacks (in GCM)

Nonce uniqueness is mandatory, not optional.

---

## Final Flag

```
bpctf{aes-gcm-crypto}
```
