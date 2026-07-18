# ComfyUI · AI Alchemy

The runtime node for **AI Alchemy** licensed ComfyUI rigs. If you bought a rig, this
node is what lets it run: it contacts the AI Alchemy licensing server with your license
key, and — if your key is valid — streams the rig's protected part into memory at runtime.

Nothing proprietary is ever written to disk or shown on the canvas.

## You probably don't need to install this manually

Every AI Alchemy rig ships with a one-click installer that adds this node for you and
points it at the right server. Just run the rig's installer. This repository exists so
the installer has a clean, versioned source to pull from.

## Manual install (advanced)

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/jtdfiber/ComfyUI_AIAlchemy
cd ComfyUI_AIAlchemy
# install deps into the SAME Python ComfyUI runs on:
python -m pip install -r requirements.txt
```

Then create a `server.json` next to `selfhost.py`:

```json
{ "server_url": "https://your-aialchemy-server" }
```

Restart ComfyUI. Open your rig, paste your license key into the **AI Alchemy · Decrypt**
node, and run. The key is saved with the workflow — you enter it once per rig.

## Using a rig

1. Load the rig's workflow (`.json`).
2. Paste your license key into the **AI Alchemy · Decrypt** node.
3. Run. Each run validates your key against the server; the protected part is rebuilt in
   RAM only. A key runs on up to 2 machines at once (cloud GPU switching is fine).

## For creators

The **AI Alchemy · Encrypt** node authorizes uploads with a `creator_token` you place in
your own `server.json`. That token stays on your encrypt machine and is never distributed
— buyers authenticate with their license key, not the creator token.

---

Derived from [CryptoCat](https://github.com/) (MIT, © RiceRound). Modifications © AI Alchemy. See `LICENSE`.
