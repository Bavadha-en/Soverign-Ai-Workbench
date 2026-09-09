import os
import re
import pytest

def test_built_frontend_exists_and_has_zero_external_runtime_urls():
    """
    Phase 4 Test: Scans the built frontend bundle in frontend/dist for unexpected external URLs.
    Allowed:
      - localhost
      - 127.0.0.1
      - Standard XML namespaces (w3.org)
      - Standard React error decoder link (static documentation string)
    Prohibited:
      - Any runtime external HTTP / HTTPS API, CDN, analytics, or remote fonts.
    """
    dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
    assert os.path.isdir(dist_dir), f"frontend/dist directory does not exist at {dist_dir}. Run 'npm run build' first."

    html_file = os.path.join(dist_dir, "index.html")
    assert os.path.exists(html_file), "frontend/dist/index.html does not exist."

    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Check for external script tags or links in index.html
    assert "googleapis.com" not in html_content, "Google Fonts or API detected in index.html"
    assert "cdn." not in html_content, "CDN link detected in index.html"
    assert "unpkg.com" not in html_content, "unpkg CDN detected in index.html"
    assert "cdnjs." not in html_content, "cdnjs CDN detected in index.html"

    # Scan all js and css assets in dist/assets
    assets_dir = os.path.join(dist_dir, "assets")
    assert os.path.isdir(assets_dir), "frontend/dist/assets does not exist."

    url_pattern = re.compile(r'https?://[a-zA-Z0-9_\-\.:/]+')
    disallowed_urls = []

    ALLOWED_HOST_PATTERNS = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "w3.org",                  # XML/SVG namespaces
        "reactjs.org/docs/error",  # React internal static minified error link
    ]

    for fname in os.listdir(assets_dir):
        fpath = os.path.join(assets_dir, fname)
        if not os.path.isfile(fpath):
            continue
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            urls = url_pattern.findall(content)
            for url in urls:
                # Check if matches allowed patterns
                is_allowed = any(allowed in url for allowed in ALLOWED_HOST_PATTERNS)
                if not is_allowed:
                    disallowed_urls.append((fname, url))

    assert len(disallowed_urls) == 0, f"Disallowed external URLs found in frontend build: {disallowed_urls}"
