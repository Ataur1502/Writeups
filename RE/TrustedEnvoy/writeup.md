# 🏛️ The Trusted Envoy — Official Write-Up

- **Category:** Mobile RE / API / OSINT
- **Difficulty:** Medium
- **Author:** ZenRage
- **Theme:** *Siege of Troy — Trust Is a Vulnerability*

---

## 📖 Challenge Summary

The city of Troy did not fall to brute force or fire, but to a **trusted envoy**. The envoy arrived carrying marks that had been trusted for generations.

The city’s systems reacted as they always had — quietly, automatically, without question. Records were consulted. Routes were considered. And somewhere between recognition and silence, something failed to surface. The mechanisms still exist. The records still speak. The paths were never erased — only assumed. What the city accepted was never displayed. What it trusted was never verified. Follow the traces the envoy would have left. Interpret what the city believed was safe.

The answer was never concealed — it was simply never meant to be seen directly.

---

## 🧠 High-Level Solution Flow
 
1. Reverse engineer the Android APK
2. Reconstruct the API request logic
3. Craft a valid request manually
4. Analyze the API response
5. Extract OSINT clues from code & resources
6. Map clues to an IXP allocation
7. Derive a specific IP address
8. Apply legacy normalization to obtain the flag

---

## 🔍 Step 1: Reverse Engineering the APK

The APK does **not** provide a usable UI path. The application either crashes or fails to retrieve data.

This signals that:

> The APK is an **artifact**, not a client.

Using tools such as:

* JADX / JADX-GUI
* apktool
* strings

Participants locate key classes:

* `ApiClient`
* `EnvoyConfig`
* `EnvoyResolver`
* Legacy codec and obfuscation logic

---

## 🌐 Step 2: Reconstructing the API Protocol

From the decompiled `ApiClient`, participants identify:

* **Endpoint:** `/envoy/status`
* **Method:** `POST`
* **Payload format:**

```json
{
  "envoy_id": "...",
  "region": "..."
}
```

This fully defines the API contract — even if the app never successfully connects.

---

## Step 3: Envoy Identifier Resolution

The application contains a deliberately convoluted resolution pipeline:

* Hardcoded legacy identifier:

```
E-IXQ-07IXO
```

* Passed through:

  * Legacy string substitutions
  * Obfuscation folds
  * Probabilistic / misleading logic
  * Final validation gate

Despite multiple rabbit holes, **only one identifier survives validation**:

```
E-IX7
```

This is the **only trusted envoy**.

---

## Step 4: Region Discovery

The region value is **not hardcoded** in visible logic.

Participants discover:

* `BuildConfig.DEPLOYMENT_REGION`
* Extracted via reverse engineering `BuildConfig.class` or Gradle metadata

Result:

```
inner-city
```

This value is required for a trusted response.

---

## Step 5: Manual API Interaction

Since the app cannot communicate reliably, participants must **craft their own request**.

Example:

```bash
curl -X POST http://<server>/envoy/status \
  -H "Content-Type: application/json" \
  -d '{"envoy_id":"E-IX7","region":"inner-city"}'
```

This returns the **trusted response**.

---

## Step 6: Analyzing the API Response

Successful response:

```json
{
  "status": "Envoy-Recognized",
  "access": "trusted-envoy",
  "log_ref": "INNER/NIXIH/IXP-07",
  "exch_region": "Secure-Channel-Region",
  "router": "secure-channel",
  "notes": "XM Transmission On activity artifact"
}
```

At this point, the challenge **shifts domains**.

---

## Step 7: Extracting Hidden OSINT Clues

Additional hints are discovered in **non-UI XML attributes** embedded inside `activity_main.xml`.  
These attributes are never rendered to the user interface but are intentionally placed as **covert OSINT indicators**:

```xml
ixp-segment="250/22"
HYD-INNER
secure-channel
```
These are **never displayed**, but intentionally embedded.

---

## Step 8: OSINT Verification (Authoritative)

From Clues (250/22, etc..), We use the APNIC WHOIS database, a IPv4 allocation owned by NIXI (National Internet eXchange of India) Hyderabad was identified:
```
inetnum: 45.250.0.0 – 45.250.3.255
CIDR:    45.250.0.0/22
netname: NIXI
country: IN
remarks: critical infrastructure
```
This confirms the block is real, Indian, and NIXI-owned exchange infrastructure.


---

## Step 9: CIDR Expansion & Index Mapping

A /22 CIDR expands into 4 contiguous /24 subnets:

```
Index	Subnet

0	45.250.0.0/24
1	45.250.1.0/24
2	45.250.2.0/24
3	45.250.3.0/24
```

The clue IXP-07 refers to an exchange segment index.

Since the CIDR allows indices 0–3, the index is normalized using modulo arithmetic:
```
7 mod 4 = 3
```
Selected subnet:
```
45.250.3.0/24
```

---

## Step 10: Host Selection

Exchange segment identifiers commonly reuse the segment index as a host identifier.

Thus:
```
45.250.3.7
```

---

## Step 11: Legacy Normalization

A final hint states:

> “Legacy gateway identifiers are stored without separators.”
Therefore, the dotted-decimal IP is normalized by removing dots:
```
45.250.3.7 → 4525037
```

---

Final Flag
```
bpctf{4525037}
```

---

## 🏛️ Final Note

Troy fell not because its walls were weak, but because its trust was never questioned. **The Trusted Envoy** was never hidden — it was simply believed.
