#!/usr/bin/env python3
"""
x-proxy.py — Post tweets via official X API or browser automation.

Method 1 (API): Set X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
Method 2 (Browser): Set X_BROWSER_MODE=1 and run Chrome with --remote-debugging-port

Auto-detects: if API keys are set, uses API. Otherwise uses browser.

Usage:
    pip install flask requests requests-oauthlib
    python x-proxy.py
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

# ── Config ───────────────────────────────────────────────────────────────────

# Method 1: Official X API (OAuth 1.0a)
X_API_KEY = os.environ.get("X_API_KEY", "").strip()
X_API_SECRET = os.environ.get("X_API_SECRET", "").strip()
X_ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "").strip()
X_ACCESS_SECRET = os.environ.get("X_ACCESS_SECRET", "").strip()

HAS_API_KEYS = all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET])

# Method 2: Browser automation via Clawdbot browser control
BROWSER_CTL_PORT = int(os.environ.get("BROWSER_CTL_PORT", 18791))
BROWSER_CTL = f"http://127.0.0.1:{BROWSER_CTL_PORT}"
X_TAB_ID = os.environ.get("X_TAB_ID", "")

# Method 2b: Browser automation via own Chrome (undetected-chromedriver)
CDP_PORT = int(os.environ.get("CDP_PORT", 9222))


# ── Method 1: Official X API ────────────────────────────────────────────────

def _post_tweet_api(text):
    """Post via official X/Twitter v2 API with OAuth 1.0a."""
    try:
        from requests_oauthlib import OAuth1Session
    except ImportError:
        return {"ok": False, "error": "requests-oauthlib not installed. Run: pip install requests-oauthlib"}

    oauth = OAuth1Session(
        X_API_KEY,
        client_secret=X_API_SECRET,
        resource_owner_key=X_ACCESS_TOKEN,
        resource_owner_secret=X_ACCESS_SECRET,
    )

    resp = oauth.post(
        "https://api.x.com/2/tweets",
        json={"text": text},
        timeout=30,
    )

    if resp.status_code in (200, 201):
        data = resp.json()
        tweet_id = data.get("data", {}).get("id", "unknown")
        return {"ok": True, "id": tweet_id, "method": "api"}
    else:
        return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:300]}", "method": "api"}


# ── Method 2: Browser automation (Clawdbot) ─────────────────────────────────

def _browser_act(action_data):
    """Send action to Clawdbot browser control."""
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


def _browser_navigate(url):
    """Navigate Clawdbot browser tab."""
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


def _post_tweet_clawdbot(text):
    """Post via Clawdbot browser compose UI."""
    if not X_TAB_ID:
        return {"ok": False, "error": "X_TAB_ID not set. Set it to the browser tab ID with x.com open."}

    # Navigate to compose
    try:
        _browser_navigate("https://x.com/compose/post")
    except Exception as e:
        return {"ok": False, "error": f"Navigate: {e}"}

    time.sleep(3)

    # Type text via JS
    safe = text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    try:
        result = _browser_act({"kind": "evaluate", "fn": f"""async () => {{
            let box = null;
            for (let i = 0; i < 20; i++) {{
                box = document.querySelector('[data-testid="tweetTextarea_0"]')
                    || document.querySelector('[contenteditable="true"][role="textbox"]');
                if (box) break;
                await new Promise(r => setTimeout(r, 300));
            }}
            if (!box) return 'NO_TEXTBOX';
            box.focus(); box.click();
            document.execCommand('insertText', false, `{safe}`);
            return 'TYPED';
        }}"""})
        if result.get("result") == "NO_TEXTBOX":
            return {"ok": False, "error": "Compose textbox not found"}
    except Exception as e:
        return {"ok": False, "error": f"Type: {e}"}

    time.sleep(1)

    # Click Post
    try:
        result = _browser_act({"kind": "evaluate", "fn": """async () => {
            const btn = document.querySelector('[data-testid="tweetButton"]');
            if (btn && !btn.disabled) { btn.click(); return 'CLICKED'; }
            const buttons = document.querySelectorAll('button');
            for (const b of buttons) {
                const span = b.querySelector('span');
                if (span && span.textContent.trim() === 'Post' && !b.disabled) { b.click(); return 'CLICKED'; }
            }
            if (btn && btn.disabled) return 'DISABLED';
            return 'NOT_FOUND';
        }"""})
        status = result.get("result", "")
        if status == "DISABLED":
            return {"ok": False, "error": "Post button disabled"}
        if status == "NOT_FOUND":
            return {"ok": False, "error": "Post button not found"}
    except Exception as e:
        return {"ok": False, "error": f"Click: {e}"}

    time.sleep(3)
    return {"ok": True, "method": "clawdbot-browser"}


# ── Method 2b: Browser automation (own Chrome) ──────────────────────────────

def _find_x_tab_cdp():
    """Find x.com tab via CDP."""
    try:
        resp = urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json", timeout=5)
        tabs = json.loads(resp.read())
        for tab in tabs:
            if "x.com" in tab.get("url", "") and tab.get("webSocketDebuggerUrl"):
                return tab
    except:
        pass
    return None


def _cdp_eval(ws_url, expression):
    """Evaluate JS via CDP websocket."""
    try:
        import websocket
    except ImportError:
        return None

    ws = websocket.create_connection(ws_url, timeout=30)
    ws.send(json.dumps({
        "id": 1,
        "method": "Runtime.evaluate",
        "params": {"expression": expression, "awaitPromise": True, "returnByValue": True}
    }))

    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            reply = json.loads(ws.recv())
            if reply.get("id") == 1:
                ws.close()
                return reply.get("result", {}).get("result", {}).get("value")
        except:
            break
    ws.close()
    return None


def _post_tweet_cdp(text):
    """Post via own Chrome browser CDP."""
    tab = _find_x_tab_cdp()
    if not tab:
        return {"ok": False, "error": f"No x.com tab found on CDP port {CDP_PORT}. Launch Chrome with --remote-debugging-port={CDP_PORT} and open x.com."}

    ws_url = tab["webSocketDebuggerUrl"]
    safe = text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

    # Navigate to compose
    _cdp_eval(ws_url, "window.location.href = 'https://x.com/compose/post'")
    time.sleep(3)

    # Type and post
    js = f"""(async () => {{
        let box = null;
        for (let i = 0; i < 20; i++) {{
            box = document.querySelector('[data-testid="tweetTextarea_0"]')
                || document.querySelector('[contenteditable="true"][role="textbox"]');
            if (box) break;
            await new Promise(r => setTimeout(r, 300));
        }}
        if (!box) return 'NO_TEXTBOX';
        box.focus(); box.click();
        document.execCommand('insertText', false, `{safe}`);
        await new Promise(r => setTimeout(r, 1000));
        const btn = document.querySelector('[data-testid="tweetButton"]');
        if (btn && !btn.disabled) {{ btn.click(); return 'POSTED'; }}
        return 'POST_FAILED';
    }})()"""

    result = _cdp_eval(ws_url, js)
    if result == "POSTED":
        return {"ok": True, "method": "cdp-browser"}
    elif result == "NO_TEXTBOX":
        return {"ok": False, "error": "Compose textbox not found"}
    else:
        return {"ok": False, "error": f"Post failed: {result}"}


# ── Router ───────────────────────────────────────────────────────────────────

def _detect_method():
    """Detect which posting method is available."""
    if HAS_API_KEYS:
        return "api"
    if X_TAB_ID:
        return "clawdbot"
    tab = _find_x_tab_cdp()
    if tab:
        return "cdp"
    return None


def _post_tweet(text):
    """Post tweet using best available method."""
    method = _detect_method()

    if method == "api":
        return _post_tweet_api(text)
    elif method == "clawdbot":
        return _post_tweet_clawdbot(text)
    elif method == "cdp":
        return _post_tweet_cdp(text)
    else:
        return {"ok": False, "error": "No posting method available. Set X API keys, X_TAB_ID for Clawdbot browser, or launch Chrome with --remote-debugging-port."}


# ── HTTP endpoints ───────────────────────────────────────────────────────────

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
    method = _detect_method()
    return jsonify({"ok": method is not None, "method": method or "none"})


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "x-proxy",
        "version": "3.1.0",
        "methods": {
            "api": "Official X API (set X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET)",
            "clawdbot": "Clawdbot browser control (set X_TAB_ID, BROWSER_CTL_PORT)",
            "cdp": "Own Chrome CDP (launch Chrome with --remote-debugging-port, open x.com, log in)",
        },
        "active": _detect_method() or "none"
    })


if __name__ == "__main__":
    port = int(os.environ.get("X_PROXY_PORT", 19877))
    method = _detect_method()
    log.info("x-proxy v3.1 on port %d | method: %s", port, method or "none")
    if HAS_API_KEYS:
        log.info("Using official X API (OAuth 1.0a)")
    elif X_TAB_ID:
        log.info("Using Clawdbot browser (tab: %s)", X_TAB_ID)
    else:
        log.info("Using CDP browser (port: %d)", CDP_PORT)
    app.run(host="127.0.0.1", port=port, debug=False)
