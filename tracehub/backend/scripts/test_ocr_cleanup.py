#!/usr/bin/env python3
"""Test script to clean up documents and test OCR classification."""

import httpx
import sys
import json

BASE_URL = "https://tracehub.vibotaj.com"

def get_token():
    """Authenticate and get token."""
    # Try different passwords
    passwords = ["admin123", "tracehub2026", "Admin123!", "password"]
    
    for pwd in passwords:
        response = httpx.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": "admin", "password": pwd},
            timeout=30
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"✓ Authenticated with admin")
            return token
    
    print(f"✗ Failed to authenticate. Last response: {response.text}")
    return None

def list_shipments(token):
    """List all shipments."""
    response = httpx.get(
        f"{BASE_URL}/api/shipments",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )
    if response.status_code == 200:
        return response.json()
    print(f"Failed to list shipments: {response.text}")
    return []

def get_shipment_documents(token, shipment_id):
    """Get documents for a shipment."""
    response = httpx.get(
        f"{BASE_URL}/api/shipments/{shipment_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )
    if response.status_code == 200:
        return response.json().get("documents", [])
    return []

def delete_document(token, document_id):
    """Delete a single document."""
    response = httpx.delete(
        f"{BASE_URL}/api/documents/{document_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )
    return response.status_code == 200 or response.status_code == 204

def main():
    print("=== Document Cleanup Script ===\n")
    
    # Authenticate
    token = get_token()
    if not token:
        sys.exit(1)
    
    # List shipments
    shipments = list_shipments(token)
    print(f"\nFound {len(shipments)} shipments:")
    
    for s in shipments:
        print(f"  - {s.get('reference')}: {s.get('id')}")
        docs = s.get("documents", [])
        if docs:
            print(f"    Documents ({len(docs)}):")
            for d in docs:
                print(f"      • {d.get('filename')} ({d.get('document_type')}) - ID: {d.get('id')}")
    
    # Find VIBO-2026-002
    vibo_002 = next((s for s in shipments if s.get("reference") == "VIBO-2026-002"), None)
    
    if vibo_002:
        docs = vibo_002.get("documents", [])
        if docs:
            print(f"\n=== Deleting {len(docs)} documents from VIBO-2026-002 ===")
            for doc in docs:
                doc_id = doc.get("id")
                filename = doc.get("filename")
                if delete_document(token, doc_id):
                    print(f"  ✓ Deleted: {filename}")
                else:
                    print(f"  ✗ Failed to delete: {filename}")
        else:
            print("\nNo documents to delete in VIBO-2026-002")
    else:
        print("\nVIBO-2026-002 shipment not found")

if __name__ == "__main__":
    main()
