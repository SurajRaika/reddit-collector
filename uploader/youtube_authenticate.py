import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


class YouTubeAuthenticator:
    def __init__(self,
                 client_secret_file: str = "client_secret.json",
                 token_file: str = "token.pickle",
                 scopes: list[str] = None):
        self.client_secret_file = client_secret_file
        self.token_file = token_file
        self.scopes = scopes or ["https://www.googleapis.com/auth/youtube.upload"]
        self.credentials = self._load_or_create_credentials()
        self.service = build("youtube", "v3", credentials=self.credentials)

    def _load_or_create_credentials(self) -> Credentials:
        creds = None

        # ✅ Load token if it exists
        if os.path.exists(self.token_file):
            with open(self.token_file, "rb") as token:
                creds = pickle.load(token)

        # 🔐 Refresh or create new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_file, self.scopes
                )
                creds = flow.run_local_server(port=8080)

            # 💾 Save the new token
            with open(self.token_file, "wb") as token:
                pickle.dump(creds, token)

        return creds

    def get_service(self):
        """Return the authenticated YouTube service object."""
        return self.service


# For manual testing
if __name__ == "__main__":
    yt_auth = YouTubeAuthenticator()
    print("✅ Authenticated and ready to use.")
