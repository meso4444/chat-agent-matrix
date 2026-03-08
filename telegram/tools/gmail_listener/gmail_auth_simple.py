#!/usr/bin/env python3
"""
Gmail OAuth 2.0 - 完全自動版本
在 WSL 中也能用：腳本啟動伺服器 → 你手動打開瀏覽器 → 腳本自動接收 token
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
print("Gmail OAuth 授權 - 自動模式")
print("=" * 60)

if not credentials_file.exists():
    print(f"❌ credentials.json 不存在")
    exit(1)

try:
    flow = InstalledAppFlow.from_client_secrets_file(
        credentials_file,
        SCOPES
    )

    print("\n🔐 啟動授權流程...\n")

    # 嘗試自動打開瀏覽器，失敗則給出 URL
    try:
        creds = flow.run_local_server(port=8080, open_browser=True)
    except Exception as browser_error:
        print(f"⚠️ 無法自動打開瀏覽器（{browser_error}）\n")

        # 生成授權 URL，啟動伺服器但不打開瀏覽器
        auth_url, _ = flow.authorization_url(prompt='consent')

        print("📖 請在你的 Windows 瀏覽器中打開這個連結：\n")
        print(f"🔗 {auth_url}\n")
        print("=" * 60)
        print("腳本正在監聽 http://localhost:8080 的授權回應...")
        print("你授權後，腳本會自動接收並保存 token\n")
        print("請在瀏覽器中點擊『允許』授權...\n")
        print("=" * 60 + "\n")

        # 啟動本地伺服器但不嘗試打開瀏覽器
        creds = flow.run_local_server(port=8080, open_browser=False)

    # 保存 token
    with open(token_file, 'w') as token:
        token.write(creds.to_json())

    print("\n✅ 授權成功！")
    print(f"✅ Token 已自動保存")
    print("\n現在可以使用 gmail_listener.py 監聽郵件了！")

except Exception as e:
    print(f"\n❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
