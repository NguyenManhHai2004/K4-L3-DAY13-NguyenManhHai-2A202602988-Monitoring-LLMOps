#!/usr/bin/env python
"""
Setup prompts in Langfuse for CP2 using REST API.
Creates day13-chat prompt with v1 (baseline+production) and v2 (candidate).
"""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent.parent / ".env")

PROMPT_NAME = "day13-chat"
PROMPT_TEMPLATE = "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}"
PROMPT_TEMPLATE_V2 = "Feature={{feature}}\nDocs={{docs}}\n\nPlease answer: {{message}}\nKeep response concise."


def make_api_call(public_key: str, secret_key: str, base_url: str, payload: dict) -> dict:
    """Make authenticated API call to Langfuse."""
    api_url = f"{base_url}/api/public/prompts"
    credentials = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def setup_prompts() -> None:
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        print("❌ Error: LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY not set in .env")
        sys.exit(1)

    print(f"🔗 Connecting to Langfuse: {base_url}")
    print(f"📝 Prompt name: {PROMPT_NAME}")

    try:
        # Create v1 with baseline + production labels
        print(f"🆕 Creating prompt '{PROMPT_NAME}' version 1...")

        v1_payload = {
            "name": PROMPT_NAME,
            "type": "text",
            "prompt": PROMPT_TEMPLATE,
            "tags": ["baseline", "production"],
            "isActive": True,
        }

        result_v1 = make_api_call(public_key, secret_key, base_url, v1_payload)
        print(f"✅ Created v1 (version: {result_v1.get('version', '?')})")
        print(f"   Labels: baseline, production")

        # Create v2 with candidate label
        print(f"🆕 Creating version 2 (candidate)...")

        v2_payload = {
            "name": PROMPT_NAME,
            "type": "text",
            "prompt": PROMPT_TEMPLATE_V2,
            "tags": ["candidate"],
            "isActive": False,
        }

        result_v2 = make_api_call(public_key, secret_key, base_url, v2_payload)
        print(f"✅ Created v2 (version: {result_v2.get('version', '?')})")
        print(f"   Label: candidate")

        print("\n" + "=" * 60)
        print("✅ SETUP COMPLETE")
        print("=" * 60)
        print(f"\nPrompt '{PROMPT_NAME}' ready for CP2:")
        print(f"  - Version 1 (labels: baseline, production)")
        print(f"  - Version 2 (label: candidate)")
        print(f"\nNext steps:")
        print(f"  1. View in Langfuse: {base_url}/project/*/prompts")
        print(f"  2. Run load test: python scripts/load_test.py")
        print(f"  3. Screenshot evidence/09-prompt-versions.png")

    except urllib.error.HTTPError as exc:
        print(f"❌ HTTP Error: {exc.code}")
        try:
            error_detail = json.loads(exc.read().decode())
            print(f"   Details: {error_detail}")
        except:
            print(f"   Response: {exc.read().decode()}")
        print(f"\nTroubleshooting:")
        print(f"  - Check LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env")
        print(f"  - Verify keys belong to project day13-k4-l3a-<MSSV>")
        print(f"  - Check internet connection to {base_url}")
        sys.exit(1)
    except Exception as exc:
        print(f"❌ Error: {exc}")
        print(f"\nTroubleshooting:")
        print(f"  - Check LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env")
        print(f"  - Verify keys belong to project day13-k4-l3a-<MSSV>")
        print(f"  - Check internet connection to {base_url}")
        sys.exit(1)


if __name__ == "__main__":
    setup_prompts()
