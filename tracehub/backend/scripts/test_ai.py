#!/usr/bin/env python3
"""Test AI document classification."""
import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

sample_text = """BILL OF LADING
B/L No: MAEU262495038
Shipper: VIBOTAJ GLOBAL VENTURES
Consignee: GERMAN IMPORTS GMBH
Container No: MAEU1234567
Port of Loading: Lagos, Nigeria
Port of Discharge: Hamburg, Germany
Description: Animal Hooves and Horns (HS Code 0506)
"""

prompt = f"""Identify the document type. Respond with JSON only.

Document:
{sample_text}

JSON response format:
{{"document_type": "bill_of_lading", "confidence": 0.95, "reference_number": "MAEU262495038"}}
"""

print("Calling Claude AI (Haiku model)...")
message = client.messages.create(
    model="claude-3-haiku-20240307",
    max_tokens=300,
    messages=[{"role": "user", "content": prompt}]
)

response = message.content[0].text
print(f"Raw response: {response}")

# Parse JSON
import re
try:
    # Try direct parse
    data = json.loads(response.strip())
except json.JSONDecodeError:
    # Try to extract JSON from response
    match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
    if match:
        data = json.loads(match.group())
    else:
        print("ERROR: Could not parse JSON from response")
        exit(1)

print("\n=== AI Classification Result ===")
print(f"Document Type: {data.get('document_type')}")
print(f"Confidence: {data.get('confidence')}")
print(f"Reference Number: {data.get('reference_number')}")
print("=== AI is working! ===")
