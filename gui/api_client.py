"""HTTP client abstraction for native Python and pygbag WASM environments.

In native mode (desktop), uses the `requests` library with synchronous calls.
In WASM mode (browser via pygbag), uses JavaScript fetch via the platform module.

Usage:
    from api_client import api_get, api_post, configure_base_url
    configure_base_url("http://localhost:8080/api")  # or relative "/api" in WASM

    data = api_post("/blackjack/start", {"bet": 100})
    state = api_get("/blackjack/state")
"""
import json
import sys

# Detect WASM environment (pygbag sets sys.platform to "emscripten")
IS_WASM = sys.platform == "emscripten"

# Base URL for API calls — configurable per environment
_base_url = ""


def configure_base_url(url: str) -> None:
    """Set the base URL for all API calls."""
    global _base_url
    _base_url = url.rstrip("/")


def _full_url(path: str) -> str:
    """Build full URL from base + path."""
    return f"{_base_url}{path}"


if IS_WASM:
    # WASM mode: use JavaScript fetch via platform module
    from platform import window  # type: ignore[attr-defined]  # noqa: E402

    def api_post(path: str, data: dict | None = None) -> dict:
        """POST request using JavaScript fetch (WASM/browser)."""
        url = _full_url(path)
        options = {
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
        }
        if data is not None:
            options["body"] = json.dumps(data)
        # Use synchronous XMLHttpRequest for compatibility with sync game code
        xhr = window.XMLHttpRequest.new()
        xhr.open("POST", url, False)  # synchronous
        xhr.setRequestHeader("Content-Type", "application/json")
        if data is not None:
            xhr.send(json.dumps(data))
        else:
            xhr.send()
        return json.loads(xhr.responseText)

    def api_get(path: str) -> dict:
        """GET request using JavaScript fetch (WASM/browser)."""
        url = _full_url(path)
        xhr = window.XMLHttpRequest.new()
        xhr.open("GET", url, False)  # synchronous
        xhr.send()
        return json.loads(xhr.responseText)

else:
    # Native mode: use requests library
    import requests

    def api_post(path: str, data: dict | None = None) -> dict:
        """POST request using requests library (native Python)."""
        url = _full_url(path)
        response = requests.post(url, data=json.dumps(data) if data else None,
                                 headers={"Content-Type": "application/json"})
        return response.json()

    def api_get(path: str) -> dict:
        """GET request using requests library (native Python)."""
        url = _full_url(path)
        response = requests.get(url)
        return response.json()
