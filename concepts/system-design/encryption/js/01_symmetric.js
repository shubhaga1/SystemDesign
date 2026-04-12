/**
 * SYMMETRIC ENCRYPTION — AES
 *
 * WHY "SYMMETRIC"?
 *   Same key used to both ENCRYPT and DECRYPT.
 *   Like a physical lock — same key locks and unlocks.
 *
 *   encrypt("hello", key) → "xK9#mP"
 *   decrypt("xK9#mP", key) → "hello"
 *   Same key both ways = SYMMETRIC
 *
 * AES (Advanced Encryption Standard):
 *   - Most widely used symmetric cipher
 *   - Key sizes: 128, 192, or 256 bits
 *   - Used for bulk data: files, database fields, HTTPS data transfer
 *
 * AES-256-GCM:
 *   256  = key size in bits (stronger)
 *   GCM  = Galois/Counter Mode (authenticated — detects tampering)
 *   IV   = Initialization Vector — random bytes to ensure same plaintext
 *          encrypts differently each time (prevents pattern analysis)
 */

const crypto = require('crypto');

// ── Generate a random 256-bit key (32 bytes) ──────────────────────────────────
const key = crypto.randomBytes(32);  // 32 bytes × 8 = 256 bits
console.log('Key (hex):', key.toString('hex'));

// ── Encrypt ───────────────────────────────────────────────────────────────────
function encrypt(plaintext, key) {
    const iv = crypto.randomBytes(16);         // random IV — new every time
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);

    let encrypted = cipher.update(plaintext, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    const authTag = cipher.getAuthTag();       // GCM auth tag — detects tampering

    // Store iv + authTag alongside ciphertext (needed for decryption)
    return {
        iv:         iv.toString('hex'),
        authTag:    authTag.toString('hex'),
        ciphertext: encrypted
    };
}

// ── Decrypt ───────────────────────────────────────────────────────────────────
function decrypt(encrypted, key) {
    const decipher = crypto.createDecipheriv(
        'aes-256-gcm',
        key,
        Buffer.from(encrypted.iv, 'hex')
    );
    decipher.setAuthTag(Buffer.from(encrypted.authTag, 'hex'));

    let decrypted = decipher.update(encrypted.ciphertext, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    return decrypted;
}

// ── Demo ──────────────────────────────────────────────────────────────────────
const message = "Hello, this is a secret message!";
console.log('\nOriginal:', message);

const encrypted = encrypt(message, key);
console.log('\nEncrypted:', encrypted);

const decrypted = decrypt(encrypted, key);
console.log('\nDecrypted:', decrypted);

// Same plaintext, different ciphertext each time (because IV is random)
const enc1 = encrypt(message, key);
const enc2 = encrypt(message, key);
console.log('\nSame message, encrypted twice:');
console.log('Enc 1:', enc1.ciphertext);
console.log('Enc 2:', enc2.ciphertext);
console.log('Different? ', enc1.ciphertext !== enc2.ciphertext);  // true — IV differs

console.log('\n--- KEY PROBLEM WITH SYMMETRIC ---');
console.log('Alice wants to send Bob an encrypted message.');
console.log('She must share the key with Bob FIRST.');
console.log('But how? If she sends it over internet, attacker intercepts it.');
console.log('→ This is the KEY DISTRIBUTION PROBLEM.');
console.log('→ Solution: Asymmetric encryption (RSA/ECC) to share the key safely.');
