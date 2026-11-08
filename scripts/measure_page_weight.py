from fastapi.testclient import TestClient
from src.web.app import app

client = TestClient(app)

def measure_web_payload():
    """
    Measures the exact byte weight of index page and all linked static assets.
    """
    # 1. HTML index
    res_html = client.get("/")
    assert res_html.status_code == 200
    html_bytes = len(res_html.content)
    
    # 2. Static CSS
    res_css = client.get("/static/style.css")
    assert res_css.status_code == 200
    css_bytes = len(res_css.content)
    
    # 3. Static JS
    res_js = client.get("/static/app.js")
    assert res_js.status_code == 200
    js_bytes = len(res_js.content)
    
    total_bytes = html_bytes + css_bytes + js_bytes
    total_kb = total_bytes / 1024.0
    
    print("=== WEB INTERFACE PAYLOAD WEIGHT MEASUREMENT ===")
    print(f"HTML (index.html):     {html_bytes:,} bytes ({html_bytes/1024:.2f} KB)")
    print(f"CSS  (style.css):      {css_bytes:,} bytes ({css_bytes/1024:.2f} KB)")
    print(f"JS   (app.js):         {js_bytes:,} bytes ({js_bytes/1024:.2f} KB)")
    print("--------------------------------------------------")
    print(f"TOTAL PAGE WEIGHT:     {total_bytes:,} bytes ({total_kb:.2f} KB)")
    print(f"LOW-BANDWIDTH TARGET:  < 50.00 KB")
    print(f"COMPLIANCE STATUS:     {'PASSED (Extremely Lightweight)' if total_kb < 50.0 else 'EXCEEDED'}")

if __name__ == "__main__":
    measure_web_payload()

