"""Minimal Sorftime MCP-over-HTTP client for box scripts.

Reads the key from env SORFTIME_KEY (fallback SORFTIME_API_KEY). Never prints the key.
Usage:
    from sorftime_http import call, call_text
    txt = call_text("keyword_detail", {"keyword": "custom leather journal", "keyword_support_site": "US"})
CLI:
    python3 sorftime_http.py keyword_detail '{"keyword":"custom leather journal","keyword_support_site":"US"}'
"""
import json, os, sys, urllib.parse, urllib.request

BASE = "https://mcp.sorftime.com"

def _key():
    k = os.environ.get("SORFTIME_KEY") or os.environ.get("SORFTIME_API_KEY")
    if not k:
        raise RuntimeError("SORFTIME_KEY env var not set")
    return k

def call(tool, arguments, timeout=60):
    """Return the MCP `result` dict (or None)."""
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": arguments}}).encode()
    url = BASE + "?" + urllib.parse.urlencode({"key": _key()})
    rq = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
    raw = urllib.request.urlopen(rq, timeout=timeout).read().decode("utf-8", "replace")
    result = None
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("data: "):
            try:
                p = json.loads(line[6:])
                if "result" in p:
                    result = p["result"]
            except json.JSONDecodeError:
                pass
    if result is None:
        try:
            result = json.loads(raw).get("result")
        except Exception:
            pass
    return result

def call_text(tool, arguments, timeout=60):
    r = call(tool, arguments, timeout)
    if not r:
        return ""
    c = r.get("content") or []
    return "\n".join(x.get("text", "") for x in c if isinstance(x, dict))

if __name__ == "__main__":
    print(call_text(sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}))
