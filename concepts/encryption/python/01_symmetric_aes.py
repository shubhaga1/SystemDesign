"""
SYMMETRIC ENCRYPTION — AES in Python

WHY "SYMMETRIC"?
  Same key used to ENCRYPT and DECRYPT.
  Like a padlock — one key both locks and unlocks.

AES-256:
  256-bit key, fastest encryption standard
  Used for: bulk data, database fields, file encryption

Install: pip install cryptography
"""

from cryptography.fernet import Fernet
import os, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ── Simple AES with Fernet (beginner-friendly) ────────────────────────────────
print("=== 1. Fernet (AES-128 under the hood, easiest API) ===")

key = Fernet.generate_key()          # generates a random key
print("Key:", key.decode()[:40] + "...")

fernet = Fernet(key)

message = b"Hello, this is a secret message!"
encrypted = fernet.encrypt(message)
print("Encrypted:", encrypted[:40], "...")

decrypted = fernet.decrypt(encrypted)
print("Decrypted:", decrypted.decode())
print("Match?", decrypted == message)

# ── AES-256-GCM (production grade) ───────────────────────────────────────────
print("\n=== 2. AES-256-GCM (production) ===")

key256 = os.urandom(32)              # 32 bytes = 256 bits
nonce  = os.urandom(12)              # 12 bytes nonce (like IV)

aesgcm = AESGCM(key256)

plaintext = b"Bank transfer: $5000 to Alice"
ciphertext = aesgcm.encrypt(nonce, plaintext, None)
print("Ciphertext:", ciphertext.hex()[:40] + "...")

recovered = aesgcm.decrypt(nonce, ciphertext, None)
print("Decrypted:", recovered.decode())

print("\n--- KEY DISTRIBUTION PROBLEM ---")
print("AES is fast but: how do Alice and Bob share the key safely?")
print("If sent over internet → attacker intercepts key → decrypts everything")
print("Solution: use RSA/ECC to share the AES key → see 02_asymmetric_rsa.py")
