#!/usr/bin/env python3
"""
Gmail OAuth 2.0 - Fully Automatic Version
Works in WSL: Script starts server → You open browser manually → Script auto-receives token
"""

import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

script_dir = Path(__file__).parent.absolute()
credentials_file = script_dir / 'credentials.json'
token_file = script_dir / 'token.json'

print("=" * 60)
print("Gmail OAuth Authorization - Automatic Mode")
print("=" * 60)

if not credentials_file.exists():
    print(f"❌ credentials.json does not exist")
    exit(1)

try:
    flow = InstalledAppFlow.from_client_secrets_file(
        credentials_file,
        SCOPES
    )

    print("\n🔐 Starting authorization flow...\n")

    # Try to auto-open browser, fall back to URL if fails
    try:
        creds = flow.run_local_server(port=8080, open_browser=True)
    except Exception as browser_error:
        print(f"⚠️ Cannot auto-open browser ({browser_error})\n")

        # Generate authorization URL, start server but don't open browser
        auth_url, _ = flow.authorization_url(prompt='consent')

        print("📖 Please open this link in your browser:\n")
        print(f"🔗 {auth_url}\n")
        print("=" * 60)
        print("Script is listening for authorization response at http://localhost:8080...")
        print("After you authorize, the script will automatically receive and save the token\n")
        print("Please click 'Allow' in the browser to authorize...\n")
        print("=" * 60 + "\n")

        # Start local server but don't try to open browser
        creds = flow.run_local_server(port=8080, open_browser=False)

    # Save token
    with open(token_file, 'w') as token:
        token.write(creds.to_json())

    print("\n✅ Authorization successful!")
    print(f"✅ Token has been automatically saved")
    print("\nYou can now use gmail_listener.py to listen for emails!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
