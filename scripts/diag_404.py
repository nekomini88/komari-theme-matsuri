"""抓出页面上所有非 200 的请求（含 404 的具体 URL），用于排查"控制台报错但没有崩"的情况。"""
import sys

from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:2602/'
bad: list[tuple[str, int]] = []
failed: list[tuple[str, str]] = []

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={'width': 1600, 'height': 900})
    pg.on('response', lambda r: bad.append((r.url, r.status)) if r.status >= 400 else None)
    pg.on('requestfailed', lambda r: failed.append((r.url, str(r.failure))))
    pg.goto(url, wait_until='networkidle', timeout=45_000)
    pg.wait_for_timeout(4000)

    print('=== 非 200 响应 ===')
    seen = {}
    for u, s in bad:
        seen[(u, s)] = seen.get((u, s), 0) + 1
    for (u, s), n in sorted(seen.items(), key=lambda x: -x[1]):
        print(f'  {s}  x{n}  {u[:130]}')
    if not seen:
        print('  无 ✓')

    print('\n=== 请求失败（网络层）===')
    seen2 = {}
    for u, f in failed:
        seen2[(u, f)] = seen2.get((u, f), 0) + 1
    for (u, f), n in sorted(seen2.items(), key=lambda x: -x[1]):
        print(f'  x{n}  {u[:110]}  -> {f[:60]}')
    if not seen2:
        print('  无 ✓')

    print('\n=== 根节点 data-* 状态 ===')
    print('  data-time =', pg.evaluate("document.documentElement.dataset.time"))
    print('  data-blur =', pg.evaluate("document.documentElement.dataset.blur"))
    print('  class     =', pg.evaluate("document.documentElement.className"))
    print('  背景图    =', pg.evaluate(
        "getComputedStyle(document.getElementById('theme-background')).backgroundImage")[:110])
    b.close()
