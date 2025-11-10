"""
DEK / KEK PATTERN — Data Encryption Key + Key Encryption Key

THE PROBLEM:
  If you encrypt all data with ONE key, that key becomes the crown jewel.
  Rotate it? Must re-encrypt terabytes of data. Leak it? Everything is exposed.

THE SOLUTION — Two-level key hierarchy:
  DEK (Data Encryption Key):
    - Encrypts the actual data (AES-256)
    - Different DEK per user/record/file
    - Lives alongside the encrypted data (but itself encrypted!)

  KEK (Key Encryption Key):
    - Encrypts the DEK (RSA-2048 or AES-256)
    - Only stored in a secure vault (AWS KMS, HashiCorp Vault, HSM)
    - Rotating KEK: decrypt all DEKs with old KEK, re-encrypt with new KEK
      (fast — DEKs are tiny, not the data itself)

USED BY:
  AWS KMS, Google Cloud KMS, Azure Key Vault, HashiCorp Vault
  Databases: Transparent Data Encryption (TDE)
  Message apps: Signal, WhatsApp (one DEK per message/session)

Install: pip install cryptography
"""

import os
import json
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

print("=" * 65)
print("DEK / KEK Pattern Demonstration")
print("=" * 65)

# ────────────────────────────────────────────────────────────────────────────
# SETUP: Key Management Service (KMS) holds the KEK (RSA key pair)
# In production: AWS KMS / HashiCorp Vault / HSM stores this securely
# ────────────────────────────────────────────────────────────────────────────
print("\n[KMS] Generating KEK (Key Encryption Key) — RSA-2048")
print("[KMS] This key NEVER leaves the KMS / vault")

kek_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
kek_public  = kek_private.public_key()
print("[KMS] KEK ready. Only KMS holds the private half.")

# ────────────────────────────────────────────────────────────────────────────
# Step 1: Generate a DEK for each user/record
# ────────────────────────────────────────────────────────────────────────────
print("\n[APP] Step 1: Generate DEK (Data Encryption Key) for user_id=42")
dek = os.urandom(32)    # 32 bytes = 256-bit AES key
print(f"  DEK (raw, plaintext): {dek.hex()[:30]}...")
print("  NEVER store DEK in plaintext!")

# ────────────────────────────────────────────────────────────────────────────
# Step 2: Encrypt the DEK with the KEK (RSA-OAEP)
# This "wrapped DEK" is what you store in the database
# ────────────────────────────────────────────────────────────────────────────
print("\n[APP → KMS] Step 2: Ask KMS to wrap (encrypt) the DEK with KEK")
wrapped_dek = kek_public.encrypt(
    dek,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
print(f"  Wrapped DEK: {wrapped_dek.hex()[:40]}...")
print(f"  Wrapped DEK size: {len(wrapped_dek)} bytes (safe to store in DB)")

# ────────────────────────────────────────────────────────────────────────────
# Step 3: Encrypt actual user data with the DEK (AES-256-GCM)
# ────────────────────────────────────────────────────────────────────────────
print("\n[APP] Step 3: Encrypt user data with DEK")

user_data = b'{"name": "Alice", "ssn": "123-45-6789", "card": "4111-1111-1111-1111"}'
print(f"  Plaintext: {user_data.decode()}")

aesgcm = AESGCM(dek)
nonce  = os.urandom(12)
encrypted_data = aesgcm.encrypt(nonce, user_data, None)
print(f"  Encrypted: {encrypted_data.hex()[:40]}...")

# ────────────────────────────────────────────────────────────────────────────
# What you store in the database (safe — DEK is wrapped, data is encrypted)
# ────────────────────────────────────────────────────────────────────────────
db_record = {
    "user_id": 42,
    "encrypted_data": encrypted_data.hex(),
    "nonce": nonce.hex(),
    "wrapped_dek": wrapped_dek.hex(),    # store alongside the data
    "kek_version": "v1"                  # track which KEK version wrapped this DEK
}
print("\n[DB] Stored record:")
print(f"  user_id:      {db_record['user_id']}")
print(f"  encrypted_data: {db_record['encrypted_data'][:30]}...")
print(f"  wrapped_dek:  {db_record['wrapped_dek'][:30]}...")
print(f"  kek_version:  {db_record['kek_version']}")
print("  (no plaintext data, no plaintext DEK anywhere in DB)")

# ────────────────────────────────────────────────────────────────────────────
# DECRYPTION FLOW: reading the data back
# ────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("DECRYPTION FLOW")
print("=" * 65)

print("\n[APP] Step 4: Read record from DB — need to decrypt")

# 4a. Ask KMS to unwrap (decrypt) the DEK using the KEK private key
print("\n[APP → KMS] Step 5: Ask KMS to unwrap DEK")
retrieved_wrapped_dek = bytes.fromhex(db_record["wrapped_dek"])
unwrapped_dek = kek_private.decrypt(
    retrieved_wrapped_dek,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
print(f"  Unwrapped DEK: {unwrapped_dek.hex()[:30]}...")
print(f"  DEK matches original? {unwrapped_dek == dek}")

# 4b. Use DEK to decrypt the data
print("\n[APP] Step 6: Decrypt user data with unwrapped DEK")
retrieved_nonce = bytes.fromhex(db_record["nonce"])
retrieved_ciphertext = bytes.fromhex(db_record["encrypted_data"])

aesgcm2 = AESGCM(unwrapped_dek)
decrypted_data = aesgcm2.decrypt(retrieved_nonce, retrieved_ciphertext, None)
print(f"  Decrypted: {decrypted_data.decode()}")

# ────────────────────────────────────────────────────────────────────────────
# KEY ROTATION — the main benefit of DEK/KEK
# ────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("KEY ROTATION — Why DEK/KEK makes this easy")
print("=" * 65)
print("""
Scenario: Rotate the KEK (e.g., yearly security policy, or compromise)

WITHOUT DEK/KEK:
  All data encrypted with ONE key → must re-encrypt TERABYTES of data
  Hours/days of downtime. Very risky.

WITH DEK/KEK:
  1. Generate new KEK (kek_v2)
  2. For each record: unwrap DEK with old KEK, re-wrap with new KEK
  3. Done! Data itself is NOT touched at all.

  DEKs are tiny (32 bytes each).
  1 million users = re-encrypt 1 million × 32 bytes = 32 MB of DEKs
  Takes seconds, not hours.

  Update db_record['kek_version'] = 'v2' after each re-wrap.
""")

print("=" * 65)
print("ARCHITECTURE SUMMARY")
print("=" * 65)
print("""
  ┌─────────────┐   wrap/unwrap DEK   ┌─────────────────┐
  │     APP     │ ◄──────────────────► │   KMS / Vault   │
  └──────┬──────┘                      │  (holds KEK)    │
         │                             └─────────────────┘
         │ encrypt/decrypt data
         ▼
  ┌─────────────┐
  │  DATABASE   │
  │  encrypted_data ← AES(DEK)  │
  │  wrapped_dek    ← RSA(KEK)  │
  └─────────────┘

  If DB is stolen:  attacker has encrypted_data + wrapped_dek
                    but NO KEK private key → cannot unwrap DEK → cannot decrypt
  If KMS is compromised: attacker has KEK
                    but still needs DB to get wrapped_dek + encrypted_data
""")
