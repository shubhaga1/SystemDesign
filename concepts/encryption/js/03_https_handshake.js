/**
 * HTTPS HANDSHAKE — Step by step simulation
 *
 * HTTPS = HTTP + TLS (Transport Layer Security)
 *
 * The handshake solves this problem:
 *   AES is fast but needs a shared key — how to share it safely?
 *   RSA can share keys safely but is too slow for bulk data.
 *   Solution: use RSA to share an AES key, then use AES for everything else.
 *
 * TLS 1.2 Handshake (RSA key exchange):
 *
 *   Client                              Server
 *     │                                   │
 *     │──── 1. ClientHello ──────────────▶│  "I support TLS 1.2, here are my ciphers"
 *     │                                   │
 *     │◀─── 2. ServerHello ───────────────│  "Use AES-256-GCM, here's my certificate"
 *     │◀─── 3. Certificate ───────────────│  Contains server's PUBLIC key
 *     │                                   │
 *     │  4. Verify certificate            │
 *     │     (is it signed by trusted CA?) │
 *     │                                   │
 *     │  5. Generate pre-master secret    │
 *     │──── 6. Encrypted pre-master ─────▶│  Encrypted with server's PUBLIC key
 *     │                                   │  Server decrypts with PRIVATE key
 *     │                                   │
 *     │  7. Both derive session key (AES) from pre-master secret
 *     │                                   │
 *     │──── 8. "Ready" (encrypted) ──────▶│
 *     │◀─── 9. "Ready" (encrypted) ───────│
 *     │                                   │
 *     │══════ All data encrypted with AES session key ══════│
 *
 * TLS 1.3 (modern — uses ECDHE instead of RSA for key exchange):
 *   Faster, Perfect Forward Secrecy — new key per session
 *   Even if private key is stolen later, past sessions can't be decrypted
 */

const crypto = require('crypto');

console.log('=== HTTPS TLS HANDSHAKE SIMULATION ===\n');

// ── Step 1 & 2: Hello messages ────────────────────────────────────────────────
console.log('STEP 1 — Client Hello');
console.log('  Client → Server: "I support TLS 1.2/1.3, AES-256-GCM, SHA-256"');
const clientRandom = crypto.randomBytes(28);
console.log('  Client random:', clientRandom.toString('hex').substring(0, 20) + '...');

console.log('\nSTEP 2 — Server Hello + Certificate');
console.log('  Server → Client: "Use AES-256-GCM. Here is my certificate."');

// ── Step 3: Server generates RSA key pair (represents certificate) ────────────
console.log('\nSTEP 3 — Server has RSA key pair (from certificate)');
const { publicKey: serverPublicKey, privateKey: serverPrivateKey } =
    crypto.generateKeyPairSync('rsa', {
        modulusLength: 2048,
        publicKeyEncoding:  { type: 'pkcs1', format: 'pem' },
        privateKeyEncoding: { type: 'pkcs1', format: 'pem' }
    });
console.log('  Server PUBLIC key sent to client (in certificate)');
console.log('  Server PRIVATE key stays on server — never leaves');

// ── Step 4: Client verifies certificate ───────────────────────────────────────
console.log('\nSTEP 4 — Client verifies certificate');
console.log('  Client checks: is this cert signed by a trusted CA?');
console.log('  (CA = Certificate Authority: DigiCert, Let\'s Encrypt, etc.)');
console.log('  Browser has built-in list of ~100 trusted CAs');
console.log('  If cert valid → continue. If not → "Your connection is not private" error');

// ── Step 5 & 6: Pre-master secret ─────────────────────────────────────────────
console.log('\nSTEP 5 — Client generates pre-master secret');
const preMasterSecret = crypto.randomBytes(46);  // 46 bytes
console.log('  Pre-master secret:', preMasterSecret.toString('hex').substring(0, 20) + '...');

console.log('\nSTEP 6 — Client encrypts pre-master with server\'s PUBLIC key');
const encryptedPreMaster = crypto.publicEncrypt(
    { key: serverPublicKey, padding: crypto.constants.RSA_PKCS1_OAEP_PADDING },
    preMasterSecret
);
console.log('  Encrypted pre-master sent to server');
console.log('  (Only server can decrypt — it has the private key)');

// ── Step 6b: Server decrypts ──────────────────────────────────────────────────
console.log('\nSTEP 6b — Server decrypts with PRIVATE key');
const decryptedPreMaster = crypto.privateDecrypt(
    { key: serverPrivateKey, padding: crypto.constants.RSA_PKCS1_OAEP_PADDING },
    encryptedPreMaster
);
console.log('  Match?', preMasterSecret.toString('hex') === decryptedPreMaster.toString('hex'));

// ── Step 7: Derive session key ────────────────────────────────────────────────
console.log('\nSTEP 7 — Both sides derive AES session key from pre-master secret');
// In real TLS: session key = PRF(pre_master_secret + client_random + server_random)
// Simplified here:
const sessionKey = crypto.createHash('sha256')
    .update(Buffer.concat([preMasterSecret, clientRandom]))
    .digest();
console.log('  Session key (AES-256):', sessionKey.toString('hex').substring(0, 20) + '...');
console.log('  Both client and server now have the SAME AES key');
console.log('  No attacker can derive it — pre-master was RSA-encrypted');

// ── Step 8 & 9: Ready ────────────────────────────────────────────────────────
console.log('\nSTEP 8-9 — Finished messages (verify handshake integrity)');
console.log('  Both send "Finished" encrypted with session key');
console.log('  Confirms: both sides derived same key correctly');

// ── Step 10: Data transfer with AES ──────────────────────────────────────────
console.log('\nSTEP 10 — Data transfer using AES session key');

function aesEncrypt(text, key) {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
    let enc = cipher.update(text, 'utf8', 'hex');
    enc += cipher.final('hex');
    return { iv: iv.toString('hex'), ciphertext: enc, tag: cipher.getAuthTag().toString('hex') };
}

function aesDecrypt(enc, key) {
    const decipher = crypto.createDecipheriv('aes-256-gcm', key, Buffer.from(enc.iv, 'hex'));
    decipher.setAuthTag(Buffer.from(enc.tag, 'hex'));
    let dec = decipher.update(enc.ciphertext, 'hex', 'utf8');
    dec += decipher.final('utf8');
    return dec;
}

const httpRequest  = 'GET /api/account HTTP/1.1\nAuthorization: Bearer secret-token-123';
const httpResponse = '{"balance": 50000, "account": "savings"}';

const encReq  = aesEncrypt(httpRequest, sessionKey);
const encResp = aesEncrypt(httpResponse, sessionKey);

console.log('  Client sends (encrypted):', encReq.ciphertext.substring(0, 40) + '...');
console.log('  Server decrypts request: ', aesDecrypt(encReq, sessionKey).substring(0, 40));
console.log('  Server sends (encrypted):', encResp.ciphertext.substring(0, 40) + '...');
console.log('  Client decrypts response:', aesDecrypt(encResp, sessionKey));

console.log('\n=== SUMMARY ===');
console.log('RSA used for:  key exchange only (1 time, during handshake)');
console.log('AES used for:  all actual data (fast, entire session)');
console.log('Why hybrid?    RSA = secure but slow | AES = fast but needs shared key');
console.log('               RSA solves AES key sharing problem');
