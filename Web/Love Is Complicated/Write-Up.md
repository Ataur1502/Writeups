# Write-Up: Love Is Complicated 💔

**Challenge Name:** Love Is Complicated  
**Category:** Web Exploitation  
**Difficulty:** Medium  
**Author:** ATLEE  
**Flag:** `BPCTF{love_is_50_Complicated_8ut_it_matt3rs}`

---

## Challenge Description

> Love is in the air... or is it? You've stumbled upon a "Love Evaluator" built by a developer who claims their love is pure and synchronized. But something feels off.
>
> Can you prove your love to the server and uncover the hidden secrets of this complicated relationship?

## Hints Provided

> **Hint 1 (0 pts):** The API does not trust your feelings. It trusts time. If access depends on "being at the right moment," ask yourself: Whose clock is being checked?

> **Hint 2 (0 pts):** Look at how the token is generated. It's not magic. It's: `HMAC(secret, timestamp + salt)`. If you know the secret… you are not guessing anything. You are calculating.

> **Hint 3 (0 pts):** The payload says "forever". Cute. Irrelevant. The real action is happening in custom headers: `x-love-time`, `x-love-token`.

---

## Step 1: Initial Reconnaissance

Navigate to the deployed challenge site at `https://valentine.breachpoint.live`. We see a Valentine-themed page with a large **"Prove Your Love"** heart button.

<!-- IMAGE: Screenshot of the Love Is Complicated landing page showing the "Prove Your Love" heart button -->

Open **Developer Tools (F12) → Network Tab** and click the button. A `POST` request is sent to `/api/confess` which returns `403 Forbidden` with the body:

```
"Love incomplete."
```

<!-- IMAGE: Screenshot of the Network tab showing the POST /api/confess request returning 403 "Love incomplete." -->

From **Hint 3**, we already know the button's payload `"forever"` is irrelevant — the real action happens in custom headers `x-love-time` and `x-love-token`.

---

## Step 2: Finding the Secret Key

We need a **secret** to calculate the HMAC token (as Hint 2 tells us). Time to inspect the frontend code.

**Method 1: Browser Console**  
Open **Developer Tools → Console Tab**. A log message is visible:

```
TODO: Remove secret 'cupid_knows_all' before deployment
```

<!-- IMAGE: Screenshot of the Console tab showing the leaked secret log message -->

**Method 2: Search the JS Bundles**  
Go to **Sources Tab → press `Ctrl+Shift+F`** to search across all files. Search for `"secret"` or `"cupid"`. This reveals the secret embedded in the bundled JavaScript:

```javascript
const fakeFlag = "BPCTF{love_is_simple}"; // Decoy!
// TODO: Remove secret 'cupid_knows_all' before deployment
```

<!-- IMAGE: Screenshot of the Sources tab search results showing the leaked secret and fake flag in the JS bundle -->

**Key Findings:**

| Item | Value | Purpose |
|------|-------|---------|
| Fake Flag (Decoy) | `BPCTF{love_is_simple}` | Trap — submitting this will fail |
| Leaked Secret Key | `cupid_knows_all` | Used for HMAC token generation |

> ⚠️ `BPCTF{love_is_simple}` is a **decoy flag**. Do not submit it!

---

## Step 3: Understanding the Time Restriction

From **Hint 1**, the API "trusts time" and access depends on *"being at the right moment."*

Using a tool like **curl** or **Postman**, we send a request with the custom headers set to dummy values:

```bash
curl -X POST https://valentine.breachpoint.live/api/confess \
  -H "Content-Type: application/json" \
  -H "x-love-time: 123456" \
  -H "x-love-token: test" \
  -d '{"message":"forever"}'
```

The server responds with:

```
"Cupid is busy. Try again between 14:00 and 14:14 UTC."
```

<!-- IMAGE: Screenshot showing the "Cupid is busy" error response in terminal or Postman -->

**Finding:** The server only accepts requests when the UTC time is between **14:00 and 14:14** — a 15-minute window.

---

## Step 4: Forging the HMAC Token

From **Hint 2**, we know the token formula:

```
HMAC(secret, timestamp + salt)
```

We already have:
- **Secret:** `cupid_knows_all` (leaked from frontend)
- **Algorithm:** HMAC-SHA256 (standard in CTFs)
- **Salt:** Needs guessing — `be_mine` fits the Valentine theme and works

So the full formula becomes:

```
x-love-token = HMAC-SHA256("cupid_knows_all", "<unix_timestamp>be_mine")
```

Quick Python verification:

```python
import hmac, hashlib

secret = b"cupid_knows_all"
timestamp = "1707919200"  # Example: 14:00 UTC
message = (timestamp + "be_mine").encode()

token = hmac.new(secret, message, hashlib.sha256).hexdigest()
print(token)
```

<!-- IMAGE: Screenshot of the Python script generating the HMAC token in a terminal -->

---

## Step 5: Avoiding the Honeypot Trap

There's a hidden trap: if you send requests **too quickly** (within 3 seconds of each other), the server returns `200 OK` with the **fake flag**:

```json
{ "flag": "BPCTF{love_is_simple}" }
```

<!-- IMAGE: Screenshot showing the fake flag being returned when requests are sent too quickly -->

The `200 OK` status makes it look legitimate — but this is a **honeypot**. The decoy flag matches the one found in the source code.

**Solution:** Wait at least **3 seconds** between requests.

---

## Step 6: Running the Final Exploit

Combining everything, we use the `exploit.py` script which:
1. Gets the server time from the response `Date` header
2. Constructs a mocked time at **14:05 UTC** (within the valid window)
3. Generates the HMAC-SHA256 token using the leaked secret
4. Sends the request with all required headers, including `x-mock-time` to bypass the time window

```bash
python exploit.py https://valentine.breachpoint.live/api/confess
```

<!-- IMAGE: Screenshot of the terminal running exploit.py -->

### The Crafted Headers:

```
x-love-time:  <unix_timestamp>        → Synchronized timestamp
x-love-token: <hmac_sha256_hex>       → Forged HMAC token
x-mock-time:  2026-02-14T14:05:00Z    → Time override (bypasses UTC window)
```

### Successful Output:

```
[*] Checking server time...
[*] Constructing Mocked Request:
    Mock Time (ISO):   2026-02-14T14:05:00+00:00
    Timestamp (Unix):  1739538300
[*] Sending Token: <hmac_hash>
[*] Status: 200
[*] Response: {"flag":"BPCTF{love_is_50_Complicated_8ut_it_matt3rs}"}

[+] Success! Flag retrieved.
```

<!-- IMAGE: Screenshot of the successful exploit output showing the real flag in the terminal -->

---

## Flag

```
BPCTF{love_is_50_Complicated_8ut_it_matt3rs}
```

---

## Vulnerabilities Exploited

| # | Vulnerability | Type |
|---|---------------|------|
| 1 | Secret key leaked in frontend JS (`cupid_knows_all`) | Information Disclosure |
| 2 | Fake flag used as decoy (`BPCTF{love_is_simple}`) | Deception / Honeypot |
| 3 | Time-based authentication window (14:00–14:14 UTC) | Logic Flaw |
| 4 | `x-mock-time` header allows server clock override | Authentication Bypass |
| 5 | HMAC token forgeable with known secret + predictable salt | Broken Cryptography |
| 6 | Rate-limit honeypot serves fake flag on rapid requests | Anti-Brute-Force Trap |

---

## Tools You'll Need

- **Browser Developer Tools** (Network, Sources, Console tabs)
- **Python 3** with `requests`, `hmac`, `hashlib` libraries
- **curl / Postman** (for manual header testing)

---

## Key Takeaways

1. **Never hardcode secrets in frontend code** — the leaked `cupid_knows_all` was the key to the entire exploit.
2. **Decoy flags waste valuable CTF time** — always verify before submitting.
3. **Rate limiting can be weaponized** — honeypot middleware serving fake responses is an effective trap.
4. **Time-based restrictions are fragile** — especially when the server accepts time-override headers.
5. **Always inspect network traffic and source code thoroughly** — the hints directly pointed to where the vulnerabilities were.
