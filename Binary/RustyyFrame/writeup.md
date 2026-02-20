# Rusty Frame --- Full Solver Write-Up

## Challenge Summary

Rusty Frame is a 64-bit PIE binary written in Rust. The program reads up
to 512 bytes from stdin and processes the input through multiple logical
gates before reaching a vulnerable stack write primitive.

Protections: - NX enabled - PIE enabled - Partial RELRO - No stack
canary

The only valid solution path is: 1. Reach `World::Real` 2. Trigger
`Layout::A` 3. Exploit stack overflow in `write_overflow_struct` 4.
Partially overwrite saved RIP 5. Redirect execution to `win()` 6. Ensure
`PROOF == MAGIC`

No ROP chain, heap exploitation, or info leak is required.

------------------------------------------------------------------------

## Step 1 --- Identify the Vulnerable Path

The input flows as:

main → process → select_world → record → record_a →
write_overflow_struct

Only `record_a()` both: - Uses the unsafe overflow primitive - Sets
global `PROOF`

Therefore, we must reach: - `World::Real` - `Layout::A`

------------------------------------------------------------------------

## Step 2 --- Satisfy World::Real

World selection logic:

-   len \< 64 → Poison
-   len & 0x60 == 0x40 → Decoy
-   Lowest byte of: (u64::from_le_bytes(data\[..8\]) \^ 0xdead_beef)
    must equal lowest byte of: ((len & 0x7f) \^ 0xdead_beef)

Since only the lowest byte matters, this constraint can be satisfied by:

1.  Choosing len \>= 64

2.  Avoiding (len & 0x60) == 0x40

3.  Solving 1-byte equation:

    data_byte0 \^ 0xef == (len & 0x7f) \^ 0xef

This simplifies to:

data_byte0 == (len & 0x7f)

Thus, first byte of input must equal (len & 0x7f).

------------------------------------------------------------------------

## Step 3 --- Trigger Layout A

Layout selection:

    (len ^ 0x1337) % 3

To reach Layout A:

    (len ^ 0x1337) % 3 == 0

We brute-force valid lengths satisfying: - len \>= 64 - Avoid Decoy
mask - Layout A condition

This reduces to a small valid length set.

------------------------------------------------------------------------

## Step 4 --- Stack Layout Analysis

FrameA structure:

struct FrameA { pad: \[u8; 16\], fake: u64, frame: \[u8; 64\], }

Saved RIP lies after struct on stack.

Empirically (via GDB): Distance from struct base to saved RIP ≈ 88
bytes.

world_offset(len) for Layout A = 72.

fake_len = offset + partial_rip_len(len)

partial_rip_len ∈ {1,2,3,4}

Thus, total overwrite length can reach saved RIP partially.

------------------------------------------------------------------------

## Step 5 --- Transform Layer

Before writing, input is transformed:

For each 4-byte chunk: - First byte XORed with 0x5a - Entire chunk
reversed

Therefore, payload must be pre-encoded so that after transform, correct
bytes appear in memory.

We implement inverse transform to encode final payload.

------------------------------------------------------------------------

## Step 6 --- Partial RIP Overwrite Strategy

PIE is enabled, so full address unknown.

However, within same binary load: Upper bytes of address remain
constant.

We overwrite only lowest 2--4 bytes of saved RIP to redirect execution
to win().

Steps:

1.  Use debugger to obtain:
    -   Address of return instruction
    -   Address of win()
2.  Compute difference in lower bytes.
3.  Overwrite only necessary trailing bytes.

------------------------------------------------------------------------

## Step 7 --- Set PROOF

Before return, we must corrupt `fake` value.

Original: 0x4141414141414141

Any change triggers: PROOF = MAGIC

Thus, ensure overflow modifies `fake` before reaching RIP.

------------------------------------------------------------------------

## Step 8 --- Exploit Construction Outline

1.  Select valid length L.
2.  data\[0\] = (L & 0x7f).
3.  Build payload:
    -   Padding to reach fake.
    -   Overwrite fake with non-0x41 pattern.
    -   Padding to reach saved RIP.
    -   Partial overwrite bytes of win().
4.  Apply inverse transform.
5.  Send payload.

------------------------------------------------------------------------

## Example Exploit Skeleton (Python)

``` python
import struct

def inverse_transform(buf):
    out = bytearray(buf)
    for i in range(0, len(out), 4):
        chunk = out[i:i+4]
        chunk.reverse()
        if len(chunk) > 0:
            chunk[0] ^= 0x5a
        out[i:i+4] = chunk
    return bytes(out)

length =  ninety_valid_length  # choose valid one
payload = bytearray(b"A" * length)

payload[0] = length & 0x7f

# Overwrite fake
payload[16:24] = b"B"*8

# Overwrite RIP low bytes
payload[88:90] = struct.pack("<H", win_low_bytes)

encoded = inverse_transform(payload)

print(encoded)
```

------------------------------------------------------------------------

## Final Control Flow

record_a() → overflow → fake corrupted → PROOF = MAGIC return → RIP →
win() win() → print flag.
