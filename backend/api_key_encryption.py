#!/usr/bin/env python3
"""
Optional: Encryption/Decryption untuk API Keys
Gunakan ini jika Anda ingin encrypt API key di database
"""

from cryptography.fernet import Fernet
import os
import base64
from pathlib import Path

class APIKeyEncryption:
    """Class untuk encrypt/decrypt API keys"""
    
    def __init__(self, key_file: str = None):
        """
        Initialize encryption
        
        Args:
            key_file: Path ke file yang berisi encryption key
                     Jika None, akan generate key baru atau load dari .env
        """
        self.key_file = key_file or Path(__file__).parent / '.api_key_encryption_key'
        self.cipher = None
        self._load_or_generate_key()
    
    def _load_or_generate_key(self):
        """Load encryption key atau generate baru"""
        # Try to load from environment variable first
        key_str = os.getenv('API_KEY_ENCRYPTION_KEY')
        
        if key_str:
            try:
                key = base64.urlsafe_b64decode(key_str.encode())
                self.cipher = Fernet(key)
                return
            except Exception as e:
                print(f"Warning: Invalid encryption key in environment: {e}")
        
        # Try to load from file
        if self.key_file.exists():
            try:
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                self.cipher = Fernet(key)
                return
            except Exception as e:
                print(f"Warning: Could not load encryption key from file: {e}")
        
        # Generate new key
        key = Fernet.generate_key()
        self.cipher = Fernet(key)
        
        # Save to file (with secure permissions)
        try:
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Set file permissions to 600 (read/write owner only)
            os.chmod(self.key_file, 0o600)
            print(f"✅ Generated new encryption key: {self.key_file}")
            print(f"⚠️  IMPORTANT: Save this key securely!")
            print(f"   Export as: export API_KEY_ENCRYPTION_KEY='{base64.urlsafe_b64encode(key).decode()}'")
        except Exception as e:
            print(f"Warning: Could not save encryption key: {e}")
    
    def encrypt(self, plain_text: str) -> str:
        """Encrypt API key"""
        if not self.cipher:
            raise ValueError("Encryption not initialized")
        
        if not plain_text:
            return ""
        
        encrypted = self.cipher.encrypt(plain_text.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt API key"""
        if not self.cipher:
            raise ValueError("Encryption not initialized")
        
        if not encrypted_text:
            return ""
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt: {e}")

# Global instance (lazy initialization)
_encryption_instance = None

def get_encryption():
    """Get global encryption instance"""
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = APIKeyEncryption()
    return _encryption_instance

def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key (convenience function)"""
    if not api_key:
        return ""
    return get_encryption().encrypt(api_key)

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key (convenience function)"""
    if not encrypted_key:
        return ""
    return get_encryption().decrypt(encrypted_key)

# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("API Key Encryption Test")
    print("=" * 60)
    
    # Test encryption
    test_key = "AIzaSyA3mUw3gtWxajpBPqB4VpFPZMf6lbnRYSU"
    print(f"\nOriginal API Key: {test_key}")
    
    encrypted = encrypt_api_key(test_key)
    print(f"Encrypted: {encrypted[:50]}...")
    
    decrypted = decrypt_api_key(encrypted)
    print(f"Decrypted: {decrypted}")
    
    if test_key == decrypted:
        print("\n✅ Encryption/Decryption works correctly!")
    else:
        print("\n❌ Encryption/Decryption failed!")

