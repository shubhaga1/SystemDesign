"""
ASYMMETRIC ENCRYPTION — RSA in Python

WHY "ASYMMETRIC"?
  Two DIFFERENT keys — one encrypts, the other decrypts.
  Public key  = share with everyone (anyone can encrypt for you)
  Private key = keep secret       (only YOU can decrypt)

RSA:
  Named after Rivest, Shamir, Adleman (1977)
  Security based on: factoring huge numbers is computationally hard
  Used for: key exchange, digital signatures, certificates

Install: pip install cryptography
"""

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

# ── 1. Generate RSA Key Pair ──────────────────────────────────────────────────
print("=== 1. Generate RSA-2048 Key Pair ===")

private_key = rsa.generate_private_key(
    public_exponent=65537,   # standard value, always use this
    key_size=2048            # 2048-bit = secure, 4096 = extra secure
)
public_key = private_key.public_key()

# Export keys as PEM strings (what you'd store in a .pem file)
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

print("Private key (first 60 chars):", private_pem.decode()[:60])
print("Public  key (first 60 chars):", public_pem.decode()[:60])

# ── 2. Encrypt with PUBLIC key → Decrypt with PRIVATE key ────────────────────
print("\n=== 2. RSA Encrypt/Decrypt ===")

message = b"Secret message from Alice to Bob"
print("Original:", message.decode())

# OAEP = Optimal Asymmetric Encryption Padding (use this, never raw RSA)
ciphertext = public_key.encrypt(
    message,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
print("Encrypted (hex):", ciphertext.hex()[:50] + "...")
print("Ciphertext length:", len(ciphertext), "bytes")  # always 256 bytes for 2048-bit RSA

# Only private key can decrypt
decrypted = private_key.decrypt(
    ciphertext,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
print("Decrypted:", decrypted.decode())
print("Match?", decrypted == message)

# ── 3. Digital Signature — Sign with PRIVATE, Verify with PUBLIC ─────────────
print("\n=== 3. Digital Signature ===")
# Signature proves: (a) data wasn't tampered, (b) sender owns the private key

document = b"Transfer $1000 to Alice — signed by Bob"

# Bob signs with his PRIVATE key
signature = private_key.sign(
    document,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)
print("Signature (hex):", signature.hex()[:50] + "...")

# Anyone with Bob's PUBLIC key can verify
try:
    public_key.verify(
        signature,
        document,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    print("Signature VALID — document is authentic")
except Exception:
    print("Signature INVALID — document was tampered!")

# Tamper test — modify the document
tampered = b"Transfer $9999 to Eve  — signed by Bob"
try:
    public_key.verify(
        signature,
        tampered,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    print("Signature VALID")
except Exception:
    print("Tamper detected — signature INVALID (expected!)")

print("\n--- RSA LIMITATION ---")
print("RSA max message size: ~190 bytes for 2048-bit key with OAEP")
print("Can't encrypt large files directly with RSA")
print("Solution: use RSA to share a small AES key, AES encrypts the file")
print("See 03_https_handshake.py and 05_dek_kek.py")
