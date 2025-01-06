from cryptography.fernet import Fernet
import keyring
import os
from platformdirs import user_data_dir
from pathlib import Path


class ApiKeyHandler:
    def __init__(self, app_name):
        self.app_name = app_name
        self.service_name = f"{self.app_name}_key"
        self.data_dir = Path(user_data_dir(self.app_name)) / "keys"

        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create directory {self.data_dir}: {e}")

    def get_fernet_key(self):
        """
        Retrieve or generate a secure key.
        """
        try:
            key = keyring.get_password(self.service_name, "encryption_key")
            if key is None:
                key = Fernet.generate_key().decode()
                keyring.set_password(self.service_name, "encryption_key", key)
            return Fernet(key.encode())
        except Exception as e:
            raise RuntimeError(f"Failed to access keyring: {e}")

    def save_api_key(self, api_key, alias):
        try:
            self.api_key_file = self.data_dir / f"{alias}.enc"
            fernet = self.get_fernet_key()
            encrypted_key = fernet.encrypt(api_key.encode())
            with open(self.api_key_file, "wb") as f:
                f.write(encrypted_key)
        except OSError as e:
            raise RuntimeError(f"Failed to write to file '{self.api_key_file}': {e}")

    def get_aliases(self):
        """
        Retrieve all available aliases from the keys directory.
        """
        return [file.stem for file in self.data_dir.glob("*.enc")]

    def load_api_key(self, alias):
        """
        Load and decrypt the API key for a given alias.
        """
        api_key_file = self.data_dir / f"{alias}.enc"
        if not api_key_file.exists():
            raise FileNotFoundError(f"No key found with alias '{alias}'.")
        try:
            fernet = self.get_fernet_key()
            with open(api_key_file, "rb") as f:
                encrypted_key = f.read()
            return fernet.decrypt(encrypted_key).decode()
        except Exception as e:
            raise RuntimeError(f"Failed to decrypt API key for alias '{alias}': {e}")

# # Example usage
# api_key = "sk-xxxxxxx"  # Replace with your actual OpenAI API key
# save_api_key(api_key)  # Save the key securely

# retrieved_key = load_api_key()
# print("Retrieved API Key:", retrieved_key)
