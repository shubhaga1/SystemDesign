# Encryption — Symmetric, Asymmetric, RSA, ECC, HTTPS

## Why the names?

```
Symmetric:   SAME key encrypts and decrypts
             Like a physical padlock — one key does both
             encrypt(data, key) → ciphertext
             decrypt(ciphertext, key) → data

Asymmetric:  TWO DIFFERENT keys — one encrypts, the other decrypts
             Public key  = encrypt (share with everyone)
             Private key = decrypt (keep secret)
             encrypt(data, publicKey) → ciphertext
             decrypt(ciphertext, privateKey) → data
```

---

## What is RSA?

Named after inventors: **R**ivest, **S**hamir, **A**dleman (1977).

Security based on: factoring large numbers is computationally hard.
```
Pick two huge primes: p = 61, q = 53
n = p × q = 3233   ← public
e = 17              ← public exponent

Public key:  (n=3233, e=17)
Private key: derived from p, q, e — only possible if you know p and q

Attacker sees n=3233 but can't find p=61, q=53 easily
(with real 2048-bit numbers, would take millions of years)
```

---

## How to generate public/private keys

```bash
# Generate RSA key pair (terminal)
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem

# Generate ECC key pair
openssl ecparam -name prime256v1 -genkey -noout -out ecc_private.pem
openssl ec -in ecc_private.pem -pubout -out ecc_public.pem

# View key contents
openssl rsa -in private.pem -text -noout
```

Or in Node.js:
```js
const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
    modulusLength: 2048,
    publicKeyEncoding:  { type: 'pkcs1', format: 'pem' },
    privateKeyEncoding: { type: 'pkcs1', format: 'pem' }
});
```

---

## HTTPS Handshake — RSA + AES (TLS 1.2)

```
Client                              Server
  │──── 1. ClientHello ────────────▶│  supported ciphers, client random
  │◀─── 2. ServerHello ─────────────│  chosen cipher, server random
  │◀─── 3. Certificate ─────────────│  server's PUBLIC key inside
  │
  │  4. Verify cert (signed by trusted CA?)
  │
  │  5. Generate pre-master secret (random bytes)
  │──── 6. Encrypt with server PUBLIC key ──▶│
  │                                          │ Decrypt with PRIVATE key
  │
  │  7. Both derive AES session key from pre-master secret
  │
  │══════ All HTTP data encrypted with AES session key ══════
```

**Why hybrid (RSA + AES)?**
```
RSA alone:  secure key exchange, but 1000x slower than AES → can't encrypt data
AES alone:  fast, but how to share the key safely over internet?
Together:   RSA shares the AES key safely, AES encrypts everything else
```

---

## RSA vs ECC

```
Feature              RSA-2048          ECC P-256
──────────────────────────────────────────────────
Security             ~112 bits         ~128 bits
Key size             2048 bits         256 bits (12x smaller)
Speed                slower            faster
Forward Secrecy      no                yes (ECDHE)
Used in              legacy HTTPS      TLS 1.3, SSH, Bitcoin, Signal
```

ECC wins because: smaller keys + faster + Perfect Forward Secrecy.
TLS 1.3 (modern HTTPS) uses ECDHE — new key pair every session.

---

## Files — run order

### JavaScript (js/ folder) — no install needed

```bash
cd js/
node 01_symmetric.js       # AES-256-GCM, key distribution problem
node 02_asymmetric_rsa.js  # RSA keygen, encrypt/decrypt, digital signature
node 03_https_handshake.js # Full TLS handshake simulation step by step
node 04_rsa_vs_ecc.js      # Key size comparison, ECDH key exchange demo
```

Uses Node.js built-in `crypto` module — no `npm install` needed.

### Python (python/ folder)

```bash
# Install once
pip install cryptography

cd python/
python 01_symmetric_aes.py  # AES with Fernet and AES-256-GCM
python 02_asymmetric_rsa.py # RSA keygen, encrypt/decrypt, digital signature
python 03_https_handshake.py # Full TLS handshake simulation
python 04_rsa_vs_ecc.py     # ECC key gen, ECDSA, ECDH key exchange
python 05_dek_kek.py        # DEK/KEK pattern — how AWS KMS works
```

### OpenSSL (terminal — built-in on Mac/Linux)

```bash
# Generate RSA key pair
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem

# Inspect a key
openssl rsa -in private.pem -text -noout

# Encrypt a file with RSA public key
openssl rsautl -encrypt -inkey public.pem -pubin -in secret.txt -out secret.enc

# Decrypt with private key
openssl rsautl -decrypt -inkey private.pem -in secret.enc -out decrypted.txt

# Generate ECC key pair (P-256)
openssl ecparam -name prime256v1 -genkey -noout -out ecc_private.pem
openssl ec -in ecc_private.pem -pubout -out ecc_public.pem

# View a certificate (e.g., from a website)
openssl s_client -connect google.com:443 -showcerts
```
