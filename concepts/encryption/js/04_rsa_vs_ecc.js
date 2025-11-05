/**
 * RSA vs ECC — Why modern systems prefer ECC
 *
 * RSA (1977):
 *   Security based on: difficulty of factoring large numbers (n = p × q)
 *   To double security: must roughly SQUARE the key size
 *   2048-bit RSA → 4096-bit RSA for 2x security
 *
 * ECC — Elliptic Curve Cryptography (1985, mainstream ~2010):
 *   Security based on: elliptic curve discrete logarithm problem
 *   Much harder problem → smaller keys for same security
 *
 * Key size comparison (same security level):
 *
 *   RSA key size    ECC key size    Security bits
 *   ────────────    ────────────    ─────────────
 *   1024 bit        ~160 bit        80  (broken)
 *   2048 bit        ~224 bit        112 (minimum)
 *   3072 bit        ~256 bit        128 (good)
 *   7680 bit        ~384 bit        192 (high)
 *   15360 bit       ~521 bit        256 (very high)
 *
 * ECC-256 = RSA-3072 in security, but key is 12x smaller
 *
 * Why ECC wins:
 *   ✅ Smaller keys → faster handshake, less CPU, less bandwidth
 *   ✅ Perfect Forward Secrecy (ECDHE) — new key per session
 *   ✅ Used by TLS 1.3, SSH, Bitcoin, Signal, WhatsApp
 *   ⚠️  More complex math — implementation bugs more dangerous
 *
 * Common ECC curves:
 *   P-256 (prime256v1) → NIST standard, used in TLS
 *   P-384              → higher security
 *   Curve25519         → modern, faster, used by Signal/WhatsApp
 *   secp256k1          → Bitcoin
 */

const crypto = require('crypto');

// ── Generate RSA key pair ─────────────────────────────────────────────────────
console.log('=== KEY GENERATION TIME ===\n');

console.time('RSA-2048 keygen');
const rsa = crypto.generateKeyPairSync('rsa', {
    modulusLength: 2048,
    publicKeyEncoding:  { type: 'pkcs1', format: 'pem' },
    privateKeyEncoding: { type: 'pkcs1', format: 'pem' }
});
console.timeEnd('RSA-2048 keygen');

// ── Generate ECC key pair ─────────────────────────────────────────────────────
console.time('ECC P-256 keygen');
const ecc = crypto.generateKeyPairSync('ec', {
    namedCurve: 'P-256',
    publicKeyEncoding:  { type: 'spki', format: 'pem' },
    privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
});
console.timeEnd('ECC P-256 keygen');

// ── Compare key sizes ─────────────────────────────────────────────────────────
console.log('\n=== KEY SIZE COMPARISON ===');
console.log('RSA-2048 public key length:  ', rsa.publicKey.length, 'chars');
console.log('ECC P-256 public key length: ', ecc.publicKey.length, 'chars');
console.log('ECC key is', Math.round(rsa.publicKey.length / ecc.publicKey.length) + 'x smaller');

// ── Sign and verify with RSA ──────────────────────────────────────────────────
console.log('\n=== SIGN/VERIFY PERFORMANCE ===');
const message = 'Transfer $1000 to Bob — timestamp: ' + Date.now();

console.time('RSA sign');
const rsaSign = crypto.createSign('SHA256');
rsaSign.update(message);
const rsaSig = rsaSign.sign(rsa.privateKey, 'base64');
console.timeEnd('RSA sign');

console.time('RSA verify');
const rsaVerify = crypto.createVerify('SHA256');
rsaVerify.update(message);
const rsaValid = rsaVerify.verify(rsa.publicKey, rsaSig, 'base64');
console.timeEnd('RSA verify');
console.log('RSA valid:', rsaValid);

// ── Sign and verify with ECC ──────────────────────────────────────────────────
console.time('ECC sign');
const eccSign = crypto.createSign('SHA256');
eccSign.update(message);
const eccSig = eccSign.sign(ecc.privateKey, 'base64');
console.timeEnd('ECC sign');

console.time('ECC verify');
const eccVerify = crypto.createVerify('SHA256');
eccVerify.update(message);
const eccValid = eccVerify.verify(ecc.publicKey, eccSig, 'base64');
console.timeEnd('ECC verify');
console.log('ECC valid:', eccValid);

// ── ECDH — key exchange (how TLS 1.3 works) ───────────────────────────────────
console.log('\n=== ECDH KEY EXCHANGE (TLS 1.3 style) ===');
console.log('Alice and Bob each generate a key pair.');
console.log('They exchange PUBLIC keys.');
console.log('Both derive the SAME shared secret without ever sending it.');

const alice = crypto.createECDH('prime256v1');
alice.generateKeys();

const bob = crypto.createECDH('prime256v1');
bob.generateKeys();

// Alice computes shared secret using Bob's public key
const aliceShared = alice.computeSecret(bob.getPublicKey());

// Bob computes shared secret using Alice's public key
const bobShared = bob.computeSecret(alice.getPublicKey());

console.log('\nAlice shared secret:', aliceShared.toString('hex').substring(0, 20) + '...');
console.log('Bob shared secret:  ', bobShared.toString('hex').substring(0, 20) + '...');
console.log('Match?', aliceShared.toString('hex') === bobShared.toString('hex'));
console.log('\nAttacker sees both public keys but CANNOT derive the shared secret.');
console.log('This is Perfect Forward Secrecy — new keys every session.');

// ── Summary ───────────────────────────────────────────────────────────────────
console.log('\n=== RSA vs ECC SUMMARY ===');
console.log(`
Feature              RSA-2048          ECC P-256
──────────────────────────────────────────────────
Security level       ~112 bits         ~128 bits
Key size             2048 bits         256 bits
Key gen speed        slower            faster
Sign speed           slower            faster
Verify speed         faster            slower
Forward Secrecy      no (RSA-only)     yes (ECDHE)
TLS 1.3 support      limited           primary
Used in              legacy HTTPS      TLS1.3, SSH, Bitcoin
`);
