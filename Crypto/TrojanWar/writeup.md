# The Trojan War Solution (Cryptography)


## Step 1 : Reconnaissance & Code Analysis

### Given Resources

#### Challenge Description:- 
```
The city sleeps beneath a veil of shadows, yet the echoes of the past whisper through the marble halls. Forgotten scrolls lie scattered, their secrets waiting for one daring enough to read between the lines.

A prince once wandered these streets, leaving behind a trail of riddles and symbols that only the cleverest mind could decipher. Each step brings you closer to the hidden truth, but only those who can see the patterns in chaos will glimpse the prize.

Legends speak of a treasure that carries a name—ancient, enduring, and coveted. The wise call it helen. Those who seek it must follow the silent currents of knowledge, trusting logic over luck, patience over haste.

The city waits. The puzzle is yours.
```
#### aes.py:-

```
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


PLAINTEXT = "REDACTED"
KEY       = "odysseus_journey"
IV        = "REDACTED"


def encrypt_aes(msg, key, iv):
    key_b = key.encode()
    iv_b  = iv.encode().ljust(16, b"\0")
    cipher = AES.new(key_b, AES.MODE_CBC, iv_b)
    return cipher.encrypt(pad(msg.encode(), AES.block_size)).hex()

cipher_hex = encrypt_aes(PLAINTEXT, KEY, IV)
print("Ciphertext:", cipher_hex)

#Ciphertext: 670c93f3661f6bc085df8793b27bd2b1e1482467d9987aa908a38a7ac0ae1855d5f4688229e9d1370ef3276c08c95d44a913943084ffb4cc9c8695fc02648f3c19c825d4bf1523d6dea0c6e0b21dd211317ad45cf1fcd9c16d003f6cd89f73de

```

AES is used in CBC mode.

key = "odysseus_journey" is known.

IV is unknown.

Ciphertext is provided.

#### rsa.py:- 

```
n = 127865920957875327059505996767912960990196675444537077314411283942162182981335766093714137663028305326541856301703598005198772891427632782294580987389690424628053057426605280464917045369569623509368612585308461187913424796767527625719781829124644644581046192216323706744363001189716381140302705185878156970459
e = 65537
c = 24885441848012775971684217685180315071153616389120044652942563794285730925141132334760627917279607107782065957587290077151211662309094636317416732303271933414956406197494080612002910414834403528383893773095397466117820296268244694924583168341285721216216715968127740616491140841070394832417137914703196886181
```

Standard RSA public key (n, e) with ciphertext c.

We do not yet know the private exponent d.

Observation:
The AES IV is likely derived from the RSA challenge; recovering it would allow decryption of the AES ciphertext.

## Step 2 : RSA Private Key Recovery

We need to recover the private key to decrypt the IV.

The modulus n is small enough to attempt factoring using a tool like msieve or yafu (or in Python using sympy’s factorint).

Once factors p and q are found:

ϕ(n)=(p−1)(q−1)

Then, the private exponent:

$d=e^{−1}modϕ(n)$

Finally, decrypt c to recover the IV:

$IV=c^{d}modn$

### Example Python code :

```
from Crypto.Util.number import long_to_bytes
from sympy import factorint

#fill with n, e, c
factors = factorint(n)
p, q = list(factors.keys())

phi = (p-1)*(q-1)
d = pow(e, -1, phi)

# Decrypt RSA ciphertext
iv_int = pow(c, d, n)
IV = long_to_bytes(iv_int)
print("Recovered IV:", IV)

```

## Step 3: AES Decryption


With the key (odysseus_journey) and recovered IV (Princess), we can decrypt the ciphertext.

```
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

cipher_hex = "670c93f3661f6bc085df8793b27bd2b1e1482467d9987aa908a38a7ac0ae1855d5f4688229e9d1370ef3276c08c95d44a913943084ffb4cc9c8695fc02648f3c19c825d4bf1523d6dea0c6e0b21dd211317ad45cf1fcd9c16d003f6cd89f73de"

key = b"odysseus_journey"
iv = b"Princess"

cipher = AES.new(key, AES.MODE_CBC, iv.ljust(16, b"\0"))
plaintext = unpad(cipher.decrypt(bytes.fromhex(cipher_hex)), AES.block_size)
print("Recovered Plaintext:", plaintext.decode())

```

The decrypted Plaintext outputs:
`Recovered Plaintext: https://drive.google.com/file/d/1BaxcxVDaPGCqRo9AFVh90AzaCE6hU42r/view?usp=drive_link`


## Step 4: The Odyssey


1. Download the file from the recovered Google Drive link.

2. Use zip2john and john to crack the ZIP password:

```
zip2john file.zip > file.hash
john file.hash --wordlist=rockyou.txt
```

## Step 5: Retrieving Helen

1. Inside the ZIP file, there is a flag.txt file:-

`OCPGS{U3y3a_15_E3ge13i3q!!!}`

2. The contents are ROT13 encrypted.

we have to use tools like cyberchef which can do it:-

```BPCTF{H3l3n_15_R3tr13v3d!!!}```
