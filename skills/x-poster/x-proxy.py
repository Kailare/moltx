#!/usr/bin/env python3
"""
x-proxy.py — Post tweets via Clawdbot browser compose UI.

Uses browser control /act endpoint to:
1. Navigate to x.com/compose/post
2. Find and type into the compose textbox
3. Click the Post button

No GraphQL, no error 226/344.
"""

import json
import os
import time
import logging
import urllib.request
from threading import Lock

from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("x-proxy")

app = Flask(__name__)
SESSION_LOCK = Lock()

BROWSER_CTL_PORT = int(os.environ.get("BROWSER_CTL_PORT", 18791))
BROWSER_CTL = f"http://127.0.0.1:{BROWSER_CTL_PORT}"
X_TAB_ID = os.environ.get("X_TAB_ID", "A5E6245AA86E0EB00CC467EBDA252CDA")


def _act(action_data):
    """Send action to browser control."""
    action_data["profile"] = "clawd"
    action_data["targetId"] = X_TAB_ID
    payload = json.dumps(action_data).encode()
    req = urllib.request.Request(
        f"{BROWSER_CTL}/act",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read())


def _navigate(url):
    """Navigate tab."""
    payload = json.dumps({
        "profile": "clawd",
        "targetId": X_TAB_ID,
        "url": url
    }).encode()
    req = urllib.request.Request(
        f"{BROWSER_CTL}/navigate",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read())


def _eval(js):
    """Evaluate JS in browser tab."""
    return _act({"kind": "evaluate", "fn": js})


def _post_tweet(text):
    """Post tweet via compose UI automation."""
    
    # 1. Navigate to compose
    log.info("Step 1: Navigate to compose")
    try:
        _navigate("https://x.com/compose/post")
    except Exception as e:
        return {"ok": False, "error": f"Navigate: {e}"}
    
    time.sleep(3)
    
    # 2. Wait for textbox and type into it via JS
    log.info("Step 2: Find textbox and type")
    safe = text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    
    try:
        result = _eval(f"""async () => {{
            // Wait for textbox
            let box = null;
            for (let i = 0; i < 20; i++) {{
                box = document.querySelector('[data-testid="tweetTextarea_0"]')
                    || document.querySelector('[contenteditable="true"][role="textbox"]');
                if (box) break;
                await new Promise(r => setTimeout(r, 300));
            }}
            if (!box) return 'NO_TEXTBOX';
            
            // Focus and click
            box.focus();
            box.click();
            
            // Use execCommand to insert text (works with contenteditable)
            document.execCommand('insertText', false, `{safe}`);
            
            return 'TYPED';
        }}""")
        
        status = result.get("result", "")
        log.info("Type result: %s", status)
        
        if status == "NO_TEXTBOX":
            return {"ok": False, "error": "Compose textbox not found"}
            
    except Exception as e:
        return {"ok": False, "error": f"Type: {e}"}
    
    time.sleep(1)
    
    # 3. Click Post button
    log.info("Step 3: Click Post")
    try:
        result = _eval("""async () => {
            // Find the Post button in the compose dialog
            const btn = document.querySelector('[data-testid="tweetButton"]');
            if (btn && !btn.disabled) {
                btn.click();
                return 'CLICKED';
            }
            // Fallback: find by text
            const buttons = document.querySelectorAll('button');
            for (const b of buttons) {
                const span = b.querySelector('span');
                if (span && span.textContent.trim() === 'Post' && !b.disabled) {
                    b.click();
                    return 'CLICKED_FALLBACK';
                }
            }
            if (btn && btn.disabled) return 'DISABLED';
            return 'NOT_FOUND';
        }""")
        
        status = result.get("result", "")
        log.info("Post button: %s", status)
        
        if status == "DISABLED":
            return {"ok": False, "error": "Post button disabled - text may not have been entered"}
        if status == "NOT_FOUND":
            return {"ok": False, "error": "Post button not found"}
            
    except Exception as e:
        return {"ok": False, "error": f"Click Post: {e}"}
    
    time.sleep(3)
    
    # 4. Check if compose closed
    try:
        result = _eval("""() => {
            const dialog = document.querySelector('[data-testid="tweetButton"]');
            return dialog ? 'STILL_OPEN' : 'CLOSED';
        }""")
        status = result.get("result", "CLOSED")
        
        if status == "CLOSED":
            log.info("Tweet posted successfully")
            return {"ok": True, "method": "compose-ui"}
        else:
            # Could still be posting, check URL
            return {"ok": True, "method": "compose-ui", "note": "dialog may still be closing"}
    except:
        return {"ok": True, "method": "compose-ui"}


@app.route("/tweet", methods=["POST"])
def tweet():
    data = request.get_json(force=True, silent=True)
    if not data or "text" not in data:
        return jsonify({"ok": False, "error": "Missing 'text'"}), 400
    text = data["text"].strip()
    if not text:
        return jsonify({"ok": False, "error": "Empty"}), 400
    if len(text) > 280:
        return jsonify({"ok": False, "error": f"Too long ({len(text)}/280)"}), 400

    log.info("Tweet (%d): %s", len(text), text[:80])
    with SESSION_LOCK:
        result = _post_tweet(text)
    log.info("=> %s", json.dumps(result)[:200])
    return jsonify(result), 200 if result.get("ok") else 500


@app.route("/status", methods=["GET"])
def status():
    try:
        r = _eval("() => document.title")
        return jsonify({"ok": True, "tab": r.get("result", "?")})
    except:
        return jsonify({"ok": False, "error": "Browser unreachable"})


@app.route("/", methods=["GET"])
def index():
    return jsonify({"service": "x-proxy", "version": "3.0.0", "method": "compose-ui"})


if __name__ == "__main__":
    port = int(os.environ.get("X_PROXY_PORT", 19877))
    log.info("x-proxy v3 on port %d", port)
    app.run(host="127.0.0.1", port=port, debug=False)
