"""
RSA vs ECC — Comparison + ECDH Key Exchange

ECC = Elliptic Curve Cryptography
  Security based on: discrete logarithm over elliptic curves
  Much harder to break than RSA for the same key size

WHY ECC WINS:
  ECC-256 bit key ≈ RSA-3072 bit key (same security, 12x smaller key)
  Faster operations (key gen, sign, verify)
  Perfect Forward Secrecy via ECDHE
  Used in: TLS 1.3, SSH, Bitcoin, Signal, WhatsApp

Install: pip install cryptography
"""

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import os

# ── 1. Key Size Comparison ─────────────────────────────────────────────────────
print("=== 1. Key Size Comparison ===")
print("""
Algorithm      | Key Size  | Security Level | Notes
───────────────────────────────────────────────────────────
RSA-2048       | 2048 bits | ~112 bits      | legacy HTTPS
RSA-3072       | 3072 bits | ~128 bits      | NIST recommended
RSA-4096       | 4096 bits | ~140 bits      | large, slow
ECC P-256      |  256 bits | ~128 bits      | TLS 1.3, modern HTTPS
ECC P-384      |  384 bits | ~192 bits      | high security
ECC P-521      |  521 bits | ~260 bits      | top security
""")

# ── 2. Generate ECC Key Pair ──────────────────────────────────────────────────
print("=== 2. Generate ECC P-256 Key Pair ===")

ecc_private = ec.generate_private_key(ec.SECP256R1())   # P-256 = SECP256R1
ecc_public  = ecc_private.public_key()

# Serialize to PEM to compare key sizes
ecc_private_pem = ecc_private.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
ecc_public_pem = ecc_public.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

print(f"ECC private key PEM size: {len(ecc_private_pem)} bytes")
print(f"ECC public  key PEM size: {len(ecc_public_pem)} bytes")
print("Compare: RSA-2048 private key PEM ≈ 1700 bytes — 10x larger!")

# ── 3. ECDSA — Digital Signature with ECC ─────────────────────────────────────
print("\n=== 3. ECDSA Digital Signature ===")

document = b"Bank transfer: $1000 to Alice"

# Sign with PRIVATE key (ECDSA = Elliptic Curve Digital Signature Algorithm)
signature = ecc_private.sign(document, ec.ECDSA(hashes.SHA256()))
print(f"Signature size: {len(signature)} bytes (vs RSA signature: 256 bytes)")
print(f"Signature (hex): {signature.hex()[:40]}...")

# Verify with PUBLIC key
try:
    ecc_public.verify(signature, document, ec.ECDSA(hashes.SHA256()))
    print("Signature VALID")
except Exception:
    print("Signature INVALID")

# ── 4. ECDH — Key Exchange (the TLS 1.3 way) ─────────────────────────────────
print("\n=== 4. ECDH Key Exchange (Elliptic Curve Diffie-Hellman) ===")
print("Alice and Bob want a shared secret without sending it over the wire")
print()

# Alice generates ephemeral key pair
alice_private = ec.generate_private_key(ec.SECP256R1())
alice_public  = alice_private.public_key()
print("Alice: generated ephemeral key pair")

# Bob generates ephemeral key pair
bob_private = ec.generate_private_key(ec.SECP256R1())
bob_public  = bob_private.public_key()
print("Bob:   generated ephemeral key pair")

# They exchange PUBLIC keys (safe to send over internet)
print("\nAlice → Bob: sends alice_public")
print("Bob → Alice: sends bob_public")

# Alice computes shared secret using Bob's PUBLIC key
alice_shared = alice_private.exchange(ec.ECDH(), bob_public)

# Bob computes shared secret using Alice's PUBLIC key
bob_shared = bob_private.exchange(ec.ECDH(), alice_public)

print(f"\nAlice's shared secret: {alice_shared.hex()[:30]}...")
print(f"Bob's   shared secret: {bob_shared.hex()[:30]}...")
print(f"Secrets match? {alice_shared == bob_shared}")

# Derive AES key from shared secret
def derive_aes_key(shared_secret: bytes) -> bytes:
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"ecdh key")
    return hkdf.derive(shared_secret)

alice_aes_key = derive_aes_key(alice_shared)
bob_aes_key   = derive_aes_key(bob_shared)
print(f"\nAES key match? {alice_aes_key == bob_aes_key}")
print("Both Alice and Bob now have the SAME AES key — attacker cannot derive it!")

# ── 5. Forward Secrecy Explained ─────────────────────────────────────────────
print("\n=== 5. Why ECDHE gives Forward Secrecy ===")
print("""
RSA TLS (no forward secrecy):
  Server has ONE long-term private key.
  If attacker records all traffic today, steals key in 5 years →
  can decrypt ALL past sessions!

ECDHE TLS (perfect forward secrecy):
  Each session generates NEW ephemeral key pair (that's the 'E' in ECDHE).
  Session key is derived, used, then DISCARDED.
  If server's long-term key is stolen → past sessions STILL safe.
  Attacker only compromises future sessions until key is rotated.

TLS 1.3 requires forward secrecy — only ECDHE and DHE allowed.
TLS 1.2 made it optional — many servers still use RSA key exchange.
""")
