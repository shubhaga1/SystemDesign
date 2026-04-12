/**
 * ASYMMETRIC ENCRYPTION — RSA
 *
 * WHY "ASYMMETRIC"?
 *   TWO different keys — one encrypts, the OTHER decrypts.
 *   Not the same key both ways = ASYMMETRIC
 *
 *   Public key  → share with everyone (encrypt with this)
 *   Private key → keep secret (decrypt with this)
 *
 *   encrypt("hello", publicKey)  → "xK9#mP..."
 *   decrypt("xK9#mP...", privateKey) → "hello"
 *   Different keys = ASYMMETRIC
 *
 * WHY PUBLIC/PRIVATE?
 *   Think of a mailbox:
 *   Public key  = the mail slot (anyone can drop mail in)
 *   Private key = the key to open the box (only you can read)
 *
 *   Anyone can encrypt → only YOU can decrypt.
 *   You can publish your public key on your website — safe.
 *
 * RSA (Rivest–Shamir–Adleman, 1977):
 *   Based on the mathematical difficulty of factoring large numbers.
 *   If n = p × q (two huge primes), finding p and q from n alone
 *   is computationally infeasible (would take millions of years).
 *
 *   Key sizes:
 *   1024 bit → broken (don't use)
 *   2048 bit → minimum acceptable today
 *   4096 bit → strong, used for certificates
 *
 * RSA weakness:
 *   SLOW — 1000x slower than AES
 *   Can only encrypt small data (limited by key size)
 *   → Never encrypt bulk data with RSA
 *   → Use RSA to encrypt the AES key only (hybrid encryption)
 */

const crypto = require('crypto');

// ── Generate RSA key pair ─────────────────────────────────────────────────────
console.log('Generating 2048-bit RSA key pair...');

const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
    modulusLength: 2048,                    // key size in bits
    publicKeyEncoding:  { type: 'pkcs1', format: 'pem' },
    privateKeyEncoding: { type: 'pkcs1', format: 'pem' }
});

console.log('\n--- PUBLIC KEY (safe to share) ---');
console.log(publicKey);

console.log('--- PRIVATE KEY (keep secret!) ---');
console.log(privateKey.substring(0, 100) + '...[truncated]');

// ── Encrypt with PUBLIC key ───────────────────────────────────────────────────
const secret = "AES-key-1234567890abcdef12345678";   // 32 bytes — an AES key
console.log('\nOriginal secret:', secret);

const encrypted = crypto.publicEncrypt(
    { key: publicKey, padding: crypto.constants.RSA_PKCS1_OAEP_PADDING },
    Buffer.from(secret)
);
console.log('\nEncrypted (base64):', encrypted.toString('base64').substring(0, 60) + '...');

// ── Decrypt with PRIVATE key ──────────────────────────────────────────────────
const decrypted = crypto.privateDecrypt(
    { key: privateKey, padding: crypto.constants.RSA_PKCS1_OAEP_PADDING },
    encrypted
);
console.log('\nDecrypted:', decrypted.toString());
console.log('Match?', decrypted.toString() === secret);

// ── Digital Signature (reverse use of keys) ───────────────────────────────────
// Sign with PRIVATE key → verify with PUBLIC key
// Proves: "only the owner of the private key sent this"
console.log('\n--- DIGITAL SIGNATURE ---');

const message = "Transfer $1000 to Bob";
const sign = crypto.createSign('SHA256');
sign.update(message);
const signature = sign.sign(privateKey, 'base64');
console.log('Signature:', signature.substring(0, 60) + '...');

// Verify
const verify = crypto.createVerify('SHA256');
verify.update(message);
const isValid = verify.verify(publicKey, signature, 'base64');
console.log('Signature valid?', isValid);  // true

// Tampered message
const verify2 = crypto.createVerify('SHA256');
verify2.update("Transfer $9999 to Bob");   // different message
const isTampered = verify2.verify(publicKey, signature, 'base64');
console.log('Tampered message valid?', isTampered);  // false

console.log('\n--- RSA SUMMARY ---');
console.log('Encrypt:   use PUBLIC key  → only private key holder can decrypt');
console.log('Sign:      use PRIVATE key → anyone with public key can verify');
console.log('Weakness:  SLOW, small data only → use RSA to share AES key, not data');
