import os.path
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Check for credentials.json (Desktop Client ID)
            creds_path = 'credentials.json'
            if not os.path.exists(creds_path):
                if os.path.exists('backend/credentials.json'):
                    creds_path = 'backend/credentials.json'
                else:
                    print("❌ ERROR: 'credentials.json' not found!")
                    print("1. Go to Google Cloud Console > APIs & Services > Credentials")
                    print("2. Create Credentials > OAuth Client ID > Desktop App")
                    print("3. Download JSON and save as 'backend/credentials.json'")
                    return

            flow = InstalledAppFlow.from_client_secrets_file(
                creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            print("✅ Success! 'token.json' generated.")
            print("The backend will now use this file to authenticate as you.")

if __name__ == '__main__':
    main()
