"""MediaWiki API client for Wikipedia read/write operations.

Authentication uses bot passwords (Special:BotPasswords), not OAuth.
Credentials: WIKIPEDIA_USERNAME and WIKIPEDIA_BOT_PASSWORD in .env

Usage:
    client = WikipediaClient()
    current = client.get_page("SOUNDEX")
    client.edit_page("SOUNDEX", new_wikitext, summary="Add primary source citations")
"""

from __future__ import annotations

import os

import requests
from dotenv import load_dotenv

_API_URL = "https://en.wikipedia.org/w/api.php"
_USER_AGENT = "Markery/0.2 (research tool; contact via account talk page)"


class WikipediaClient:
    def __init__(self) -> None:
        load_dotenv()
        self._username = os.environ.get("WIKIPEDIA_USERNAME", "").strip()
        self._password = os.environ.get("WIKIPEDIA_BOT_PASSWORD", "").strip()
        self._session  = requests.Session()
        self._session.headers["User-Agent"] = _USER_AGENT
        self._logged_in = False

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def login(self) -> None:
        """Authenticate with bot password. Called lazily before edits."""
        if self._logged_in:
            return
        if not self._username or not self._password:
            raise RuntimeError(
                "WIKIPEDIA_USERNAME and WIKIPEDIA_BOT_PASSWORD must be set in .env"
            )

        token_resp = self._session.get(_API_URL, params={
            "action": "query", "meta": "tokens", "type": "login", "format": "json",
        })
        token_resp.raise_for_status()
        login_token = token_resp.json()["query"]["tokens"]["logintoken"]

        login_resp = self._session.post(_API_URL, data={
            "action": "login",
            "lgname":     self._username,
            "lgpassword": self._password,
            "lgtoken":    login_token,
            "format":     "json",
        })
        login_resp.raise_for_status()
        result = login_resp.json()["login"]["result"]
        if result != "Success":
            raise RuntimeError(f"Wikipedia login failed: {result}")
        self._logged_in = True

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_page(self, title: str) -> str | None:
        """Return current wikitext for a page, or None if it doesn't exist."""
        resp = self._session.get(_API_URL, params={
            "action":    "query",
            "titles":    title,
            "prop":      "revisions",
            "rvprop":    "content",
            "rvslots":   "main",
            "format":    "json",
            "formatversion": "2",
        })
        resp.raise_for_status()
        pages = resp.json()["query"]["pages"]
        page  = pages[0]
        if page.get("missing"):
            return None
        return page["revisions"][0]["slots"]["main"]["content"]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def _csrf_token(self) -> str:
        resp = self._session.get(_API_URL, params={
            "action": "query", "meta": "tokens", "format": "json",
        })
        resp.raise_for_status()
        return resp.json()["query"]["tokens"]["csrftoken"]

    def edit_page(self, title: str, wikitext: str, summary: str) -> dict:
        """Replace the full wikitext of a page. Returns the API response."""
        self.login()
        token = self._csrf_token()
        resp = self._session.post(_API_URL, data={
            "action":  "edit",
            "title":   title,
            "text":    wikitext,
            "summary": summary,
            "token":   token,
            "format":  "json",
            "bot":     "false",
        })
        resp.raise_for_status()
        return resp.json()

    def append_section(self, title: str, section_title: str, content: str, summary: str) -> dict:
        """Append a new section to an existing page."""
        self.login()
        token = self._csrf_token()
        resp = self._session.post(_API_URL, data={
            "action":       "edit",
            "title":        title,
            "section":      "new",
            "sectiontitle": section_title,
            "text":         content,
            "summary":      summary,
            "token":        token,
            "format":       "json",
            "bot":          "false",
        })
        resp.raise_for_status()
        return resp.json()
