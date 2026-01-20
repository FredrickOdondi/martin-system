#!/usr/bin/env python3
"""
Refresh Google OAuth Token Script

This script refreshes the expired Google Calendar OAuth token using the refresh token.
It updates the local token.json file and provides the command to update Railway.
"""

import json
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_FILE = 'token.json'

def refresh_token():
    """Refresh the OAuth token using the refresh token."""
    
    if not os.path.exists(TOKEN_FILE):
        print(f"❌ Error: {TOKEN_FILE} not found!")
        print("Please ensure token.json exists in the current directory.")
        return False
    
    try:
        # Load existing credentials
        print(f"📖 Loading credentials from {TOKEN_FILE}...")
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        # Check if token is expired
        if not creds.expired:
            print("✅ Token is still valid!")
            print(f"   Expiry: {creds.expiry}")
            return True
        
        # Check if we have a refresh token
        if not creds.refresh_token:
            print("❌ Error: No refresh token available!")
            print("You need to re-authenticate using the full OAuth flow.")
            return False
        
        # Refresh the token
        print("🔄 Token expired. Refreshing...")
        print(f"   Old expiry: {creds.expiry}")
        
        creds.refresh(Request())
        
        print("✅ Token refreshed successfully!")
        print(f"   New expiry: {creds.expiry}")
        
        # Save the refreshed token
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        
        print(f"💾 Saved refreshed token to {TOKEN_FILE}")
        
        # Read the token JSON for Railway update
        with open(TOKEN_FILE, 'r') as token:
            token_json = token.read()
        
        # Escape for shell
        token_json_escaped = token_json.replace('"', '\\"')
        
        print("\n" + "="*80)
        print("📋 NEXT STEP: Update Railway Environment Variable")
        print("="*80)
        print("\nRun this command to update Railway:\n")
        print(f'railway variables set GOOGLE_TOKEN_JSON="{token_json_escaped}"')
        print("\nOr copy this JSON and update manually in Railway dashboard:")
        print("-"*80)
        print(token_json)
        print("-"*80)
        
        return True
        
    except Exception as e:
        print(f"❌ Error refreshing token: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*80)
    print("Google OAuth Token Refresh Script")
    print("="*80)
    print()
    
    success = refresh_token()
    
    if success:
        print("\n✅ Token refresh completed successfully!")
    else:
        print("\n❌ Token refresh failed. Please check the errors above.")
        exit(1)
