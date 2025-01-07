from cryptography.fernet import Fernet
import keyring
from pathlib import Path
from platformdirs import user_data_dir


class SecretHandler:
    def __init__(self, app_name) -> None:
        self.app_name = app_name
        self.service_name = f"{self.app_name}_key"
        self.data_dir = Path(user_data_dir(self.app_name)) / "keys"

        self.google_credential_name = "credentials_GCC.enc"

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

    def save_api_key(self, api_key, alias) -> None:
        try:
            api_key_file = self.data_dir / f"{alias}_API.enc"
            fernet = self.get_fernet_key()
            encrypted_key = fernet.encrypt(api_key.encode())
            with open(api_key_file, "wb") as f:
                f.write(encrypted_key)
        except OSError as e:
            raise RuntimeError(f"Failed to write to file '{api_key_file}': {e}")

    def get_aliases(self) -> list:
        """
        Retrieve all available aliases from the keys directory.
        """
        filenames = [file.stem for file in self.data_dir.glob("*_API.enc")]
        return [f.rstrip("_API") for f in filenames]

    def load_api_key(self, alias) -> str:
        """
        Load and decrypt the API key for a given alias.
        """
        api_key_file = self.data_dir / f"{alias}_API.enc"
        if not api_key_file.exists():
            raise FileNotFoundError(f"No key found with alias '{alias}'.")
        try:
            fernet = self.get_fernet_key()
            with open(api_key_file, "rb") as f:
                encrypted_key = f.read()
            return fernet.decrypt(encrypted_key).decode()
        except Exception as e:
            raise RuntimeError(f"Failed to decrypt API key for alias '{alias}': {e}")
        
    def save_google_credential(self, credential) -> None:
        try:
            credential_file = self.data_dir / self.google_credential_name
            fernet = self.get_fernet_key()
            encrypted_key = fernet.encrypt(credential.encode())
            with open(credential_file, "wb") as f:
                f.write(encrypted_key)
        except OSError as e:
            raise RuntimeError(f"Failed to write to file '{credential_file}': {e}")
        
    def load_google_credential(self) -> str:
        """
        Load and decrypt the API key for a given alias.
        """
        credential_file = self.data_dir / self.google_credential_name
        if not credential_file.exists():
            raise FileNotFoundError(f"No credential file found.")
        try:
            fernet = self.get_fernet_key()
            with open(credential_file, "rb") as f:
                encrypted_key = f.read()
            return fernet.decrypt(encrypted_key).decode()
        except Exception as e:
            raise RuntimeError(f"Failed to decrypt credential file: {e}")
