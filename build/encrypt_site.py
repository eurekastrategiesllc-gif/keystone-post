"""Lock the published site behind an access code.

Usage: SITE_PASSCODE=... python3 build/encrypt_site.py _site
Every JSON data file under <dir>/site is gzipped and encrypted (AES-256-GCM, key
derived from the access code with PBKDF2-SHA256) and written as <name>.json.enc;
the readable file is removed. site/lock.json tells the page to ask for the code.
"""
import os, sys, gzip, json, base64, hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ITER = 600000
SALT = hashlib.sha256(b'keystone-post access code salt v1').digest()[:16]

def main(root):
    code = os.environ.get('SITE_PASSCODE', '').strip()
    if not code: sys.exit('SITE_PASSCODE is empty')
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT, iterations=ITER).derive(code.encode('utf-8'))
    box = AESGCM(key)
    def seal(b):
        iv = os.urandom(12); return iv + box.encrypt(iv, b, None)
    n = 0
    for d, _, files in os.walk(os.path.join(root, 'site')):
        for f in files:
            if not f.endswith('.json'): continue
            p = os.path.join(d, f)
            open(p + '.enc', 'wb').write(seal(gzip.compress(open(p, 'rb').read(), 6)))
            os.remove(p); n += 1
    lock = {'v': 1, 'salt': base64.b64encode(SALT).decode(), 'iter': ITER, 'check': base64.b64encode(seal(b'keystone-post')).decode()}
    json.dump(lock, open(os.path.join(root, 'site', 'lock.json'), 'w'))
    print('locked %d data files' % n)

if __name__ == '__main__':
    main(sys.argv[1])
