#!/usr/bin/env python3
"""
Google Calendar OAuth Setup
Generates token.json for Calendar API access
"""
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/calendar']

def main():
    creds = None
    
    # Check if token exists
    if os.path.exists('token.json'):
        print("Removing expired token...")
        os.remove('token.json')
    
    # Check for credentials file
    if not os.path.exists('google_credentials.json'):
        print("ERROR: google_credentials.json not found!")
        print("Please ensure you have the OAuth credentials file.")
        return
    
    # Run OAuth flow
    print("Starting OAuth flow...")
    print("A browser window will open. Please authorize the application.")
    
    flow = InstalledAppFlow.from_client_secrets_file(
        'google_credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Save the credentials
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    
    print("✅ Success! token.json created.")
    print("Restart your backend server to use the new credentials.")

if __name__ == '__main__':
    main()
