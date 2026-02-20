<div align="center">

# Quantum Crypto Challenge 1 — **BB84, But Lazy**

**Category:** Quantum Cryptography
**Difficulty:** Medium–Hard
**Flag format:** `bpctf{hex}`
**Author:** ZenRage

</div>

---

## Challenge Summary

The challenge presents a simulated **BB84 Quantum Key Distribution** session.
Alice and Bob attempt to establish a shared secret key, but the implementation contains a subtle flaw.

As an eavesdropper (Eve), we are given a capture of the protocol transcript and must recover the final shared key.

---

## Given Files

```
README.txt
capture.log
```

* `README.txt` gives minimal story context.
* `capture.log` contains the full intercepted transcript.

No quantum hardware or physics simulation is required — this is a **protocol-level attack**.

---

## Understanding the Data (`capture.log`)

Each line in `capture.log` has the format:

```
index  alice_bit+basis  bob_basis  bob_result  KEEP/DROP
```

Example:

```
42 1Z X 0 DROP
```

Meaning:

* Alice sent bit `1` using basis `Z`
* Bob measured using basis `X`
* Bob got result `0`
* Bases didn’t match → discarded during sifting

This matches standard **BB84 public discussion**.

---

## Step 1 — Parse the Capture Log

We begin by parsing the log defensively (real logs are messy).

```python
records=[]
with open("capture.log") as f:
    for line in f:
        line=line.strip()
        if not line:
            continue
        parts=line.split()
        if len(parts)!=5:
            continue
        idx,alice_enc,bob_basis,bob_res,status=parts
        records.append({
            "i":int(idx),
            "alice_bit":int(alice_enc[0]),
            "alice_basis":alice_enc[1],
            "bob_basis":bob_basis,
            "bob_res":int(bob_res),
            "keep":status=="KEEP"
        })
print("Total records:",len(records))
```

Output:

```
Total records: 2048
```

So we have 2048 qubit transmissions.

---

## Step 2 — Sanity Check: Is BB84 Mostly Correct?

Before attacking, we verify that the protocol is not completely broken.

We compute the error rate among **kept bits**:

```python
kept=[r for r in records if r["keep"]]
errors=sum(r["bob_res"]!=r["alice_bit"] for r in kept)
print("Kept bits:",len(kept))
print("Error rate:",errors/len(kept))
```

Output:

```
Kept bits: 1057
Error rate: ~0.018
```

This low error rate indicates:

* No active eavesdropping
* Noise is present but small
* BB84 is *mostly* implemented correctly

So the flaw must be **subtle**.

---

## Step 3 — Key Insight

In **correct BB84**:

> The probability of a bit being `KEEP` is **independent of its index**.

If Alice reuses bases periodically, then:

> `KEEP/DROP` probability becomes **index-dependent**.

This is the weakness we exploit.

---

## Step 4 — Detect Periodic Bias

We test candidate periods `k = 2…19`.

For each `k`, we:

* Group indices by `i % k`
* Compute KEEP rate per group
* Measure **spread = max(rate) − min(rate)**

```python
from collections import defaultdict
def score_period(k):
    buckets=defaultdict(list)
    for r in records:
        buckets[r["i"]%k].append(r["keep"])
    rates=[sum(b)/len(b) for b in buckets.values()]
    return max(rates)-min(rates),rates
for k in range(2,20):
    spread,_=score_period(k)
    print(f"k={k:2d} spread={spread:.4f}")
```

Output (excerpt):

```
k=13 spread=0.1519
k=15 spread=0.1723
k=17 spread=0.1702
k=18 spread=0.2124
```

Large spread ⇒ strong bias ⇒ candidate reuse period.

---

## Step 5 — Rank Candidate Periods

Instead of guessing, we **rank statistically**:

```python
candidates=sorted(
    [(k,score_period(k)[0]) for k in range(2,20)],
    key=lambda x:-x[1]
)
print(candidates[:5])
```

Output:

```
[(18,0.2124),(15,0.1723),(17,0.1702),(16,0.1562),(13,0.1519)]
```

These are **hypotheses**, not answers.

---

## Step 6 — Recover Alice’s Basis Pattern

For each candidate `k`, we infer which basis Alice used at each position `i % k`.

Key idea:

* When Bob’s basis matches Alice’s, Bob’s result matches Alice’s bit (except noise).
* We count which basis (`Z` or `X`) gives more correct results.

```python
def infer_basis_pattern(k):
    pattern=[]
    for pos in range(k):
        subset=[r for r in records if r["i"]%k==pos and r["keep"]]
        if not subset:
            pattern.append("?")
            continue
        z_correct=sum(r["bob_basis"]=="Z" and r["bob_res"]==r["alice_bit"] for r in subset)
        x_correct=sum(r["bob_basis"]=="X" and r["bob_res"]==r["alice_bit"] for r in subset)
        pattern.append("Z" if z_correct>x_correct else "X")
    return pattern
for k,_ in candidates[:5]:
    print(f"k={k} pattern={''.join(infer_basis_pattern(k))}")
```

Output:

```
k=18 pattern=ZXZZXXZXZZXXZXZZXX
k=15 pattern=ZXZZXXZXZZXXZXZ
k=17 pattern=ZZXZZZXXZZXXZXZXX
k=16 pattern=ZXZXZXZXZXZXZXZX
k=13 pattern=XZZXXZZZZXZZX
```

---

## Step 7 — Choose the Real Period

Observations:

* `k=16` is unrealistically symmetric → harmonic artifact
* `k=17`, `k=13` look noisy
* `k=18` appears to be `k=15` plus a noisy tail
* `k=15` shows a **clean, repeating structure**

## Why only **k = 15** and **k = 18** survive (and why 15 is correct)

After detecting statistically significant bias in the BB84 transcript, the solver ranks candidate reuse periods by the **spread of KEEP probability** across indices modulo `k`.

This yields the strongest candidates:

```
k = 18 (spread ≈ 0.212)
k = 15 (spread ≈ 0.172)
k = 17 (spread ≈ 0.170)
k = 16 (spread ≈ 0.156)
k = 13 (spread ≈ 0.152)
```

At this stage, **statistics alone are insufficient**.
Large spread only tells us *that something repeats* — not *what the real generator is*.

To proceed, the solver must analyze **structure**, not just magnitude.

---

## Structural analysis of inferred basis patterns

For each candidate `k`, we infer Alice’s basis choice at each position `i mod k` by checking which basis (`Z` or `X`) produces more correct results among the kept bits.

This produces the following inferred patterns:

```
k = 18 → ZXZZXXZXZZXXZXZZXX
k = 15 → ZXZZXXZXZZXXZXZ
k = 17 → ZZXZZZXXZZXXZXZXX
k = 16 → ZXZXZXZXZXZXZXZX
k = 13 → XZZXXZZZZXZZX
```

Now we reason carefully.

---

## Why **k = 16** is rejected (perfect symmetry = artifact)

```
ZXZXZXZXZXZXZXZX
```

This pattern is **too perfect**:

* Exact alternation
* No noise
* No irregularity
* Full symmetry

Such patterns are **not produced by lazy reuse**.
They are a known effect of **modulo aliasing**, where:

* the tested period accidentally aligns opposite halves of a smaller real period
* producing artificial symmetry

This is a **harmonic artifact**, not a generator.

**Conclusion:**
`k = 16` explains *bias*, but not *cause*. Reject.

---

## Why **k = 13** and **k = 17** are rejected (noise-dominated projections)

```
k = 13 → XZZXXZZZZXZZX
k = 17 → ZZXZZZXXZZXXZXZXX
```

Problems:

* No repeating motif
* Long unbalanced runs
* Inconsistent structure
* High sensitivity to noise

These occur when:

* the tested period is *close* to the real one
* but misaligned
* causing partial matches that smear structure

In cryptanalysis terms:

> These are **projections** of the real period through an incorrect modulus.

They reflect **statistical shadowing**, not true reuse.

**Conclusion:**
`k = 13` and `k = 17` are false positives. Reject.

---

## Why **k = 15** is the real reuse period

```
ZXZZXX | ZXZZXX | ZXZ
```

This pattern shows:

* Clear internal repetition (`ZXZZXX`)
* Imperfect tail (expected due to noise + finite data)
* Balanced basis usage
* Stable inference across the dataset

This is exactly what we expect from:

> Alice reusing a fixed basis string lazily in BB84.

This pattern:

* Explains the KEEP/DROP bias
* Produces the longest clean raw key
* Is structurally consistent

**Conclusion:**
`k = 15` is the true reuse period.

---

## Why **k = 18** also looks valid (and must be tested)

```
ZXZZXX | ZXZZXX | ZXX
```

Compare carefully:

```
k = 15 → ZXZZXX | ZXZZXX | ZXZ
k = 18 → ZXZZXX | ZXZZXX | ZXX
```

What’s happening?

### Harmonic explanation

* True reuse period = 15
* Testing modulo 18:

  * aligns with the real pattern for two full blocks
  * leaves a noisy remainder
* This produces **partial structural agreement**

This is a **harmonic alias**:

* `18` is not the generator
* but it is statistically compatible with the generator

Therefore:

> `k = 18` is not correct — but it cannot be rejected *a priori*.

---

## Why the solver must try **both 15 and 18**

At this point, the solver has two **legitimate hypotheses**:

```
H₁: reuse period = 15 (true)
H₂: reuse period = 18 (harmonic alias)
```

There is **no statistical test** that conclusively eliminates `18` without key recovery.

So a correct solver:

1. Derives the raw key for both
2. Hashes each candidate
3. Outputs both flags
4. Lets validation decide

This is **not guessing** — it is **hypothesis testing under noise**, exactly as in real cryptanalysis.

---

## Final resolution

When both keys are derived:

```
period = 18 → bpctf{cf50…}  (partialyy valid)
period = 15 → bpctf{5ca6…}  (accepted)
```

Thus:

* `k = 18` explains *some* bias
* `k = 15` explains **everything**

```
period ∈ {15, 18}
```

Due to noise, **both are plausible**, so a correct solver tries both.

---

## Step 8 — Recover the Raw Key & Final Flag

For each candidate period:

* Keep bits where inferred Alice basis matches Bob’s basis
* Hash raw key using SHA-256

```python
import hashlib
for period,_ in candidates[:2]:
    pattern=infer_basis_pattern(period)
    raw_bits=[]
    for r in records:
        if pattern[r["i"]%period]==r["bob_basis"]:
            raw_bits.append(str(r["bob_res"]))
    final_key=hashlib.sha256("".join(raw_bits).encode()).hexdigest()
    print(f"period={period} FLAG=bpctf{{{final_key}}}")
```

Output:

```
period=18 FLAG=bpctf{cf50d18c54e5585e60573d9aec05c4f35ca3d19a58cf096407361ff7dcc1b41a}
period=15 FLAG=bpctf{5ca602eab1151737a7ead99125ea49660da75c2266b6b88cb0fe5eb532d7ac50}
```

---

## Final Answer

```
> can be both or any one acc to ctf platform availability. 

bpctf{cf50d18c54e5585e60573d9aec05c4f35ca3d19a58cf096407361ff7dcc1b41a}
bpctf{5ca602eab1151737a7ead99125ea49660da75c2266b6b88cb0fe5eb532d7ac50}
```
