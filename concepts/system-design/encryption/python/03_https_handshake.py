"""
HTTPS HANDSHAKE SIMULATION — TLS 1.2 step by step

WHAT HAPPENS when browser opens https://google.com?
  1. Client says hello (what ciphers I support)
  2. Server sends its certificate (contains public key)
  3. Client verifies certificate (signed by trusted CA?)
  4. Client generates a secret, encrypts with server's PUBLIC key
  5. Server decrypts with PRIVATE key → both have same secret
  6. Both derive an AES session key from that secret
  7. All HTTP data is now AES-encrypted

WHY HYBRID (RSA + AES)?
  RSA: secure key exchange, but ~1000x slower than AES → can't encrypt all data
  AES: blazing fast, but needs a shared key
  Together: RSA safely shares the AES key, AES encrypts everything else

Install: pip install cryptography
"""

import os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

print("=" * 60)
print("TLS 1.2 Handshake Simulation")
print("=" * 60)

# ── STEP 1: Server has a certificate (RSA key pair) ───────────────────────────
print("\n[SERVER] Generating RSA-2048 key pair (normally done once, stored in cert)...")
server_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
server_public  = server_private.public_key()
print("[SERVER] Ready. Public key will be sent in certificate.")

# ── STEP 2: ClientHello ────────────────────────────────────────────────────────
print("\n[CLIENT → SERVER] Step 1: ClientHello")
client_random = os.urandom(28)     # 28 random bytes + 4 bytes timestamp
print(f"  client_random: {client_random.hex()[:20]}...")
print("  Supported ciphers: TLS_RSA_WITH_AES_256_GCM_SHA384")

# ── STEP 3: ServerHello + Certificate ─────────────────────────────────────────
print("\n[SERVER → CLIENT] Step 2: ServerHello + Certificate")
server_random = os.urandom(32)
print(f"  server_random: {server_random.hex()[:20]}...")
print("  Chosen cipher: TLS_RSA_WITH_AES_256_GCM_SHA384")
print("  Sending certificate with PUBLIC KEY...")
# In real TLS: certificate is signed by a CA (Certificate Authority)
# Browser has CA's public key pre-installed → can verify the cert

# ── STEP 4: Client verifies certificate ───────────────────────────────────────
print("\n[CLIENT] Step 3: Verify certificate")
print("  Checking: Is this cert signed by a trusted CA? (simulated: YES)")
print("  Checking: Is hostname matching? (simulated: YES)")
print("  Certificate trusted. Proceeding.")

# ── STEP 5: Client generates pre-master secret, encrypts with server's pub key
print("\n[CLIENT] Step 4: Generate pre-master secret")
pre_master_secret = os.urandom(48)   # 48 random bytes
print(f"  pre_master_secret: {pre_master_secret.hex()[:20]}... (NEVER sent in plaintext)")

print("\n[CLIENT → SERVER] Step 5: Send encrypted pre-master secret")
encrypted_pms = server_public.encrypt(
    pre_master_secret,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
print(f"  encrypted_pms: {encrypted_pms.hex()[:30]}... (RSA-encrypted, safe to send)")

# ── STEP 6: Server decrypts pre-master secret ─────────────────────────────────
print("\n[SERVER] Step 6: Decrypt pre-master secret with PRIVATE key")
decrypted_pms = server_private.decrypt(
    encrypted_pms,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
print(f"  Decrypted pre_master_secret: {decrypted_pms.hex()[:20]}...")
print(f"  Match? {decrypted_pms == pre_master_secret}")

# ── STEP 7: Both sides derive the same AES session key ────────────────────────
print("\n[CLIENT + SERVER] Step 7: Derive AES session key (same on both sides)")
# Both have: pre_master_secret + client_random + server_random
# PRF (Pseudo-Random Function) combines them into a master secret
master_secret_input = pre_master_secret + client_random + server_random

# Use HKDF to derive a 32-byte AES key (simulates TLS PRF)
hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"tls session key")
session_key = hkdf.derive(master_secret_input)

print(f"  session_key: {session_key.hex()[:30]}...")
print("  CLIENT has this key. SERVER has this key. Attacker does NOT.")

# ── STEP 8: Encrypted communication ───────────────────────────────────────────
print("\n[CLIENT → SERVER] Step 8: HTTP request (AES-256-GCM encrypted)")
aesgcm = AESGCM(session_key)
nonce = os.urandom(12)

http_request = b"GET /account HTTP/1.1\r\nHost: bank.com\r\nCookie: session=abc123"
encrypted_request = aesgcm.encrypt(nonce, http_request, None)
print(f"  Encrypted: {encrypted_request.hex()[:40]}...")

# Server decrypts
http_received = aesgcm.decrypt(nonce, encrypted_request, None)
print(f"\n[SERVER] Decrypted request: {http_received.decode()[:50]}...")

print("\n" + "=" * 60)
print("HANDSHAKE COMPLETE")
print("=" * 60)
print("""
Summary:
  RSA (asymmetric): used ONCE to exchange the pre-master secret
  AES (symmetric):  used for ALL data (fast, stream encryption)

  Even if attacker records the encrypted traffic, they need:
  → server's private key to get pre_master_secret
  → which lets them derive session_key
  → which lets them decrypt everything

  TLS 1.3 improvement: uses ECDHE (Elliptic Curve Diffie-Hellman)
  → new key pair per session → forward secrecy
  → even if private key is stolen later, past sessions stay safe
  → see 04_rsa_vs_ecc.py
""")
