from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import json
from pathlib import Path

from secret_handler import SecretHandler

class GoogleAuthHandler:

    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    CREDENTIALS_FILE = 'credentials.json'

    def __init__(self, app_name):
        self.app_name = app_name
        self.port = 19536
        self.secret_handler = SecretHandler(self.app_name)

    def get_credentials(self) -> Credentials:
        """
        Get or refresh Google API credentials.

        Returns:
            Credentials object.
        """
        try:
            # Retrieve the stored credentials
            token = self.load_google_credential()

            try:
                # Load and decrypt the credentials
                token_data = json.loads(token)
                creds = Credentials.from_authorized_user_info(token_data, GoogleAuthHandler.SCOPES)
            except Exception as e:
                print(f"Failed to load credentials from keyring: {e}")

            # Refresh the credentials if they are expired
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

        except FileNotFoundError:
            pass

        # Check for the existence of credentials.json before authenticating
        if not Path(GoogleAuthHandler.CREDENTIALS_FILE).exists():
            raise FileNotFoundError(f"Required file '{GoogleAuthHandler.CREDENTIALS_FILE}' not found.")
        
        # Run the authentication flow if no valid credentials are found
        creds = self.authenticate_with_browser()

        # Save the credentials
        json_creds = creds.to_json()
        self.secret_handler.save_google_credential(json_creds)         

        return creds
        
    def authenticate_with_browser(self):
        """
        Authenticate the user using OAuth 2.0 and return credentials.
        """
        flow = InstalledAppFlow.from_client_secrets_file(
            GoogleAuthHandler.CREDENTIALS_FILE, self.SCOPES
        )
        # Run local server for OAuth 2.0 redirect
        creds = flow.run_local_server(port=self.port)
        return creds
        
    def save_google_credential(self, credential) -> None:
        """
        Encrypt and save google credentials.
        """
        self.secret_handler.save_google_credential(credential)

    def load_google_credential(self) -> str:
        """
        Load and decrypt the API key for a given alias.
        """
        return self.secret_handler.load_google_credential()
        
    @staticmethod
    def are_credentials_valid(creds):
        """
        Check if credentials are valid and usable.
        """
        return creds and not creds.expired
