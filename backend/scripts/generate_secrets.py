import secrets
import base64
import os
from cryptography.fernet import Fernet

def generate_secrets():
    print("--- TaxFlow Production Secrets Generator ---\n")
    
    # 1. JWT Secret Key
    jwt_secret = secrets.token_urlsafe(64)
    print(f"JWT_SECRET_KEY (copy this to your environment variables):")
    print(f"{jwt_secret}\n")
    
    # 2. Fernet Encryption Key
    # Fernet keys must be 32 url-safe base64-encoded bytes.
    encryption_key = Fernet.generate_key().decode()
    print(f"ENCRYPTION_KEY (primary key for exchange credentials):")
    print(f"{encryption_key}\n")
    
    print("--- SECURITY TIPS ---")
    print("1. Store these in your hosting provider's 'Environment Variables' or 'Secrets' section.")
    print("2. NEVER commit these to your Git repository.")
    print("3. To ROTATE your encryption key: move the current ENCRYPTION_KEY to ENCRYPTION_KEYS (list),")
    print("   and generate a NEW one to be the primary ENCRYPTION_KEY.")
    print("---------------------------------------------")

if __name__ == "__main__":
    generate_secrets()
