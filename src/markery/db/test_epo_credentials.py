#!/usr/bin/env python3
"""
Smoke-test for EPO OPS API credentials and basic patent search.
Run this once after adding EPO_CONSUMER_KEY and EPO_CONSUMER_SECRET to .env.

Usage:
    python src/markery/db/test_epo_credentials.py
"""

import base64
import os
import json
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

KEY    = os.getenv("EPO_CONSUMER_KEY")
SECRET = os.getenv("EPO_CONSUMER_SECRET")

if not KEY or not SECRET:
    print("ERROR: EPO_CONSUMER_KEY and EPO_CONSUMER_SECRET must be set in .env")
    sys.exit(1)

AUTH_URL   = "https://ops.epo.org/3.2/auth/accesstoken"
SEARCH_URL = "https://ops.epo.org/3.2/rest-services/published-data/search"


# ── 1. Obtain access token ────────────────────────────────────────────────────

print("1. Authenticating with EPO OPS ...")
creds = base64.b64encode(f"{KEY}:{SECRET}".encode()).decode()
r = requests.post(
    AUTH_URL,
    headers={
        "Authorization": f"Basic {creds}",
        "Content-Type":  "application/x-www-form-urlencoded",
    },
    data="grant_type=client_credentials",
    timeout=15,
)

if r.status_code != 200:
    print(f"   FAIL  {r.status_code}: {r.text[:300]}")
    sys.exit(1)

token = r.json()["access_token"]
expires_in = r.json().get("expires_in", "?")
print(f"   OK    token obtained (expires in {expires_in}s)")


# ── 2. Look up a known patent by publication number ───────────────────────────

print("\n2. Fetching biblio for US1261167 (Russell Soundex, 1918) ...")
biblio_url = "https://ops.epo.org/3.2/rest-services/published-data/publication/epodoc/US1261167/biblio"
r2 = requests.get(
    biblio_url,
    headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    timeout=15,
)
print(f"   Status: {r2.status_code}")
if r2.status_code == 200:
    data = r2.json()
    # Dig out title and applicant from OPS response structure
    try:
        pub = data["ops:world-patent-data"]["exchange-documents"]["exchange-document"]
        bib = pub["bibliographic-data"]
        title = bib["invention-title"]
        if isinstance(title, list):
            title = title[0]
        title_text = title.get("#text", title) if isinstance(title, dict) else title
        print(f"   Title: {title_text}")
    except (KeyError, TypeError):
        print("   (could not parse title from response)")
    print(f"   Raw (truncated): {json.dumps(data)[:400]}")
else:
    print(f"   {r2.text[:400]}")


# ── 3. CQL search: US patents, CPC class B42F, 1918 ──────────────────────────

print("\n3. CQL search: cpc=B42F, US patents, granted 1918 ...")
r3 = requests.get(
    SEARCH_URL,
    headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "X-OPS-Range": "1-5",
    },
    params={"q": 'cpc=B42F AND pd within "19180101,19181231" AND pn=US'},
    timeout=15,
)
print(f"   Status: {r3.status_code}")
if r3.status_code == 200:
    data = r3.json()
    try:
        result_range = data["ops:world-patent-data"]["ops:biblio-search"]["@total-result-count"]
        print(f"   Total matching: {result_range}")
        docs = data["ops:world-patent-data"]["ops:biblio-search"]["ops:search-result"]["exchange-documents"]
        if not isinstance(docs, list):
            docs = [docs]
        for doc in docs[:5]:
            d = doc.get("exchange-document", doc)
            if isinstance(d, list):
                d = d[0]
            pn = d.get("@doc-number", "?")
            country = d.get("@country", "")
            kind = d.get("@kind", "")
            print(f"   {country}{pn}{kind}")
    except (KeyError, TypeError) as e:
        print(f"   (could not parse results: {e})")
        print(f"   Raw: {json.dumps(data)[:600]}")
else:
    print(f"   {r3.text[:400]}")

print("\nDone.")
