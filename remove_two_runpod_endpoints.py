#!/usr/bin/env python3
"""
Delete exactly two specified RunPod serverless endpoints and their templates.
- Endpoints:
  - vllm-jeyzs2mtqtcrx1 (template: vp48krsbig)
  - vllm-pw2h94fjhm9rvf (template: kpyzl33u48)

Requires env var RUNPOD_API_KEY. Loads .env if present.
"""
import os
import sys
import json
import time
import requests

# Load .env if present (works reliably in a standalone script)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
if not RUNPOD_API_KEY:
    print("❌ RUNPOD_API_KEY not set. Aborting.")
    sys.exit(1)

# GraphQL endpoint (use .io, not .ai)
GRAPHQL_URL = "https://api.runpod.io/graphql"
HEADERS = {"Authorization": f"Bearer {RUNPOD_API_KEY}", "Content-Type": "application/json"}

# Targets
ENDPOINTS = [
    {"id": "vllm-jeyzs2mtqtcrx1", "name": "qwen-1.7b-vllm-lora", "template_id": "vp48krsbig"},
    {"id": "vllm-pw2h94fjhm9rvf", "name": "qwen-1.7b-vllm-lora-fixed", "template_id": "kpyzl33u48"},
]


def gql(query: str, variables: dict | None = None) -> dict:
    resp = requests.post(GRAPHQL_URL, headers=HEADERS, json={"query": query, "variables": variables or {}}, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"GraphQL HTTP {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return data["data"]


def delete_endpoint(endpoint_id: str) -> bool:
    """Delete a serverless endpoint by ID using GraphQL."""
    # Correct signature returns Void and takes id: String!
    mutations = [
        ("mutation($id: String!){ deleteEndpoint(id: $id) }", {"id": endpoint_id}),
        ("mutation($id: ID!){ deleteEndpoint(id: $id) }", {"id": endpoint_id}),
    ]
    last_err = None
    for q, vars in mutations:
        try:
            gql(q, vars)
            return True
        except Exception as e:
            last_err = e
    print(f"⚠️ Failed to delete endpoint {endpoint_id}: {last_err}")
    return False


def delete_template(template_id: str) -> bool:
    """Delete a template by ID using GraphQL."""
    mutations = [
        # Arg name observed as templateId; returns Void
        ("mutation($id: String!){ deleteTemplate(templateId: $id) }", {"id": template_id}),
        ("mutation($id: ID!){ deleteTemplate(templateId: $id) }", {"id": template_id}),
    ]
    last_err = None
    for q, vars in mutations:
        try:
            gql(q, vars)
            return True
        except Exception as e:
            last_err = e
    print(f"⚠️ Failed to delete template {template_id}: {last_err}")
    return False


def sdk_list_endpoints_index() -> dict:
    """List endpoints via RunPod SDK for reliable verification."""
    try:
        import runpod
        runpod.api_key = RUNPOD_API_KEY
        eps = runpod.get_endpoints()
        return {ep.get("id"): ep for ep in eps}
    except Exception as e:
        print(f"⚠️ SDK list endpoints failed: {e}")
        return {}


if __name__ == "__main__":
    print("🔧 Deleting specified RunPod endpoints and templates...")

    before = sdk_list_endpoints_index()
    for ep in ENDPOINTS:
        ep_id = ep["id"]
        tpl_id = ep["template_id"]
        name = ep["name"]

        exists = ep_id in before
        print(f"\n— Endpoint: {name} ({ep_id}) | Template: {tpl_id} | Exists: {exists}")

        # Delete endpoint first
        ok_ep = delete_endpoint(ep_id)
        print(f"   Delete endpoint: {'✅' if ok_ep else '❌'}")

        # Best effort short wait
        time.sleep(1)

        # Delete template
        ok_tpl = delete_template(tpl_id)
        print(f"   Delete template: {'✅' if ok_tpl else '❌'}")

    # Verify removal
    time.sleep(2)
    after = sdk_list_endpoints_index()

    removed = []
    remaining = []
    for ep in ENDPOINTS:
        if ep["id"] not in after:
            removed.append(ep["id"])
        else:
            remaining.append(ep["id"])

    print("\n📋 Verification:")
    print(f"   Removed: {', '.join(removed) if removed else 'None'}")
    print(f"   Still present: {', '.join(remaining) if remaining else 'None'}")

    # Exit code to reflect result
    if remaining:
        sys.exit(2)
    sys.exit(0)
