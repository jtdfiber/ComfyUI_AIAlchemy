"""Self-host config for the AI Alchemy node.

Reads server.json sitting next to this file:
  { "server_url": "https://...", "creator_token": "..." }

server_url    — your licensing server (both encrypt + decode talk to it)
creator_token — ONLY on your encrypt machine (authorizes uploading a rig).
                Buyers' installs omit it; decode uses the buyer's key, not this.
"""

import json
import os

_CFG = None


def _load():
    global _CFG
    if _CFG is None:
        p = os.path.join(os.path.dirname(__file__), "server.json")
        _CFG = {}
        if os.path.exists(p):
            try:
                _CFG = json.load(open(p, encoding="utf-8"))
            except Exception:
                _CFG = {}
    return _CFG


def server_url():
    return (_load().get("server_url") or "http://127.0.0.1:8791").rstrip("/")


def creator_token():
    return _load().get("creator_token", "")
