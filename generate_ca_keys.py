from secure_med_trans.security.cryptography.ca import CertificateAuthority

priv, pub = CertificateAuthority.generate_ca_keys()

import os
os.makedirs("keys", exist_ok=True)

with open("keys/ca_private.pem", "wb") as f:
    f.write(priv)

with open("keys/ca_public.pem", "wb") as f:
    f.write(pub)

print("✅ CA keys generated successfully")