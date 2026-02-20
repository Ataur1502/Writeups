<div align="center">

# ChallengeCrypto4 - Fractured RSA WriteUp

</div>

## 1. Challenge Overview

We are given:

-   Public exponent\
    $$e = 65537$$

-   RSA modulus\
    $$n = pq$$ 
    where $p$ and $q$ are 2048-bit primes.

- Ciphertext\
    $$c = m^e \bmod n$$

- A leak\
    $$\texttt{leak} = \varphi(n) \bmod 2^k$$ with $k = 784$.

The modulus is 4096 bits. Direct factorization is infeasible.

The attack exploits the modular leakage of $\varphi(n)$.

------------------------------------------------------------------------

## 2. Key RSA Identity

Recall:

$$
\varphi(n) = (p-1)(q-1)
$$

Expand:

$$
\varphi(n) = pq - p - q + 1
$$

Since $pq = n$:

$$
\varphi(n) = n - (p+q) + 1
$$

Rearrange:

$$
p + q = n - \varphi(n) + 1
$$

Thus, $\varphi(n)$ determines the sum of primes.

If we know $S = p+q$, we factor instantly via:

$$
x^2 - Sx + n = 0
$$

------------------------------------------------------------------------

## 3. Interpreting the Leak

We are given:

$$
\varphi(n) \equiv \texttt{leak} \pmod{2^k}
$$

So:

$$
\varphi(n) = \texttt{leak} + t \cdot 2^k
$$

for some unknown integer $t$.

Substitute into the prime sum identity:

$$
p+q = n - (\texttt{leak} + t2^k) + 1
$$

$$
p+q = (n - \texttt{leak} + 1) - t2^k
$$

Define:

$$
S_0 = n - \texttt{leak} + 1
$$

Thus:

$$
p+q \equiv S_0 \pmod{2^k}
$$

------------------------------------------------------------------------

## 4. Prime Sum Approximation

Balanced RSA primes satisfy:

$$
p \approx q \approx \sqrt{n}
$$

Thus:

$$
p+q \approx 2\sqrt{n}
$$

Compute approximation:

``` python
from math import isqrt
approx_S = 2 * isqrt(n)
```

------------------------------------------------------------------------

## 5. Constrained Arithmetic Progression

We know:

$$
S = S_0 + t 2^k
$$

Compute:

``` python
mod = 1 << k
S0 = (n - leak + 1) % mod
```

Compute approximate $t$:

``` python
t0 = (approx_S - S0) // mod
```

------------------------------------------------------------------------

## 6. Searching for Correct Prime Sum

``` python
from math import isqrt

for dt in range(-5000, 5000):
    t = t0 + dt
    S = S0 + t * mod

    D = S*S - 4*n
    if D < 0:
        continue

    r = isqrt(D)
    if r*r == D:
        p = (S + r) // 2
        q = (S - r) // 2
        if p*q == n:
            print("Factorization found")
            break
```

------------------------------------------------------------------------

## 7. Recovering the Private Key

``` python
phi = (p - 1) * (q - 1)

from Crypto.Util.number import inverse
d = inverse(e, phi)
```

------------------------------------------------------------------------

## 8. Decrypting the Ciphertext

``` python
from Crypto.Util.number import long_to_bytes

m = pow(c, d, n)
flag = long_to_bytes(m)
print(flag)
```

Output:

    bpctf{crypto_found}

------------------------------------------------------------------------

## 9. Security Lessons

-   $\varphi(n)$ must remain completely secret.
-   Even modular fragments of $\varphi(n)$ are catastrophic.
-   Low-bit leakage of $\varphi(n)$ leaks low bits of $p+q$.
-   Knowing most bits of $p+q$ collapses factoring complexity.
