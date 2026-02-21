# rust_safe --- Writeup

**Category:** Reverse Engineering\
**Difficulty:** Easy / Medium\
**Artifact Provided:** Compiled ELF Binary Only

------------------------------------------------------------------------

## 1. Challenge Overview

The binary accepts a string via standard input and prints either:

    Correct!

or

    Wrong!

No source code is provided to the solver. The goal is to reverse
engineer the executable and determine the correct input string that
satisfies the internal validation logic.

------------------------------------------------------------------------

## 2. Initial Reconnaissance

### File Identification

``` bash
file hello_rust
```

Output:

    ELF 64-bit LSB executable, x86-64

This confirms a 64-bit Linux binary.

------------------------------------------------------------------------

## 3. Static Analysis

Since only the binary is provided, we load it into:

-   Ghidra
-   IDA Pro
-   Binary Ninja

Rust binaries are large and noisy due to static linking and iterator
abstractions, so we focus only on:

-   String references
-   Numeric constants
-   The comparison block leading to `"Correct!"`

------------------------------------------------------------------------

## 4. Locating the Validation Logic

Search for:

-   `"Correct!"`
-   `"Wrong!"`
-   The constant `7699` (decimal)

```{=html}
<!-- -->
```
    7699 decimal = 0x1E13

Tracing cross-references to this comparison leads to the validation
routine.

------------------------------------------------------------------------

## 5. Reconstructed Logic

After simplifying the iterator-heavy Rust decompilation, the core logic
becomes:

``` rust
let r = input
    .trim()
    .chars()
    .enumerate()
    .map(|(i, c)| (c as u32) ^ (i as u32))
    .filter(|v| v & 1 == 0)
    .fold(0x1337u32, |a, v| a.wrapping_add(v << 1));

if r == 7699 {
    println!("Correct!");
}
```

------------------------------------------------------------------------

## 6. Mathematical Reduction

Let the input string be:

    s = s₀ s₁ s₂ ... sₙ

For each character:

    v_i = ord(s_i) ^ i

Only values where:

    v_i % 2 == 0

are kept.

The accumulator starts at:

    0x1337 = 4919

Each valid value contributes:

    v_i << 1 = 2 * v_i

Therefore:

    r = 4919 + 2 * Σ(v_i)

We require:

    r = 7699

So:

    4919 + 2S = 7699
    2S = 2780
    S = 1390

Thus the constraint becomes:

    Σ (ord(s_i) ^ i) = 1390

with every term even.

------------------------------------------------------------------------

## 7. Parity Constraint

A value `(ord(s_i) ^ i)` is even when:

    LSB(ord(s_i)) == LSB(i)

Meaning:

-   If index is even → character ASCII must be even
-   If index is odd → character ASCII must be odd

------------------------------------------------------------------------

## 8. Solving Strategy

We must construct a string such that:

    Σ (ord(s_i) ^ i) = 1390

Subject to parity constraints.

One approach:

-   Choose a string length
-   Enforce parity per index
-   Solve as a constrained integer problem

------------------------------------------------------------------------

## 9. Provided Solution

The correct input is:

    bababqpqpw

Flag format:

    BPCTF{bababqpqpw}

------------------------------------------------------------------------

## 10. Verification Procedure

To verify correctness:

``` bash
echo bababqpqpw | ./hello_rust
```

Expected output:

    Correct!

------------------------------------------------------------------------

## 11. Why This Challenge Works

This challenge tests:

-   Reverse engineering Rust binaries
-   Understanding functional iterator chains
-   Translating `.map()`, `.filter()`, `.fold()` into algebra
-   XOR properties
-   Parity reasoning
-   Arithmetic constraint solving

It contains:

-   No memory corruption
-   No anti-debugging
-   No obfuscation
-   Pure deterministic logic reversal

------------------------------------------------------------------------

## 12. Final Insight

The validation is entirely mathematical.\
Once reduced to:

    Σ (ord(s_i) ^ i) = 1390

the problem becomes straightforward constraint solving.

The key takeaway:

Functional iterator chains in Rust often compile into arithmetic
patterns that are easier to reason about mathematically than
structurally.

------------------------------------------------------------------------

**Final Flag:**

    BPCTF{bababqpqpw}
