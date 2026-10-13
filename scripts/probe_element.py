"""剖开一个对比度不足的元素：打印它自己的计算色 + 整条祖先链的背景/模糊，定位真凶。"""
import sys

from playwright.sync_api import sync_playwright

TARGET = sys.argv[2] if len(sys.argv) > 2 else '延迟'
url = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:2602/'

JS = """
(target) => {
  const walk = (el, depth) => {
    const cs = getComputedStyle(el);
    return {
      depth,
      tag: el.tagName.toLowerCase(),
      cls: (el.className || '').toString().slice(0, 70),
      text: (el.textContent || '').trim().slice(0, 24),
      color: cs.color,
      bg: cs.backgroundColor,
      bd: cs.backdropFilter || cs.webkitBackdropFilter || '',
      filter: cs.filter,
      opacity: cs.opacity,
      vars: {
        mutedFg: cs.getPropertyValue('--muted-foreground').trim(),
        cardBg: cs.getPropertyValue('--node-card-bg').trim(),
        dataBg: cs.getPropertyValue('--node-data-bg').trim(),
        offline: cs.getPropertyValue('--node-offline-bg').trim(),
      },
    };
  };
  const all = [...document.querySelectorAll('*')].filter(
    (e) => e.children.length === 0 && (e.textContent || '').trim() === target
  );
  if (!all.length) return { found: false };
  const el = all[0];
  const chain = [];
  let cur = el;
  while (cur && chain.length < 8) {
    chain.push(walk(cur, chain.length));
    cur = cur.parentElement;
  }
  return { found: true, chain };
}
"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={'width': 1600, 'height': 900})
    pg.goto(url, wait_until='networkidle', timeout=45_000)
    pg.wait_for_timeout(4000)
    r = pg.evaluate(JS, TARGET)
    if not r.get('found'):
        print(f'  未找到文案 «{TARGET}»')
    else:
        for n in r['chain']:
            print(f"  [{n['depth']}] <{n['tag']}> {n['cls']}")
            print(f"        text={n['text']!r} color={n['color']} bg={n['bg']}")
            print(f"        backdrop={n['bd'][:60]} filter={n['filter'][:40]} opacity={n['opacity']}")
            v = n['vars']
            print(f"        vars: muted-foreground={v['mutedFg']} node-card-bg={v['cardBg']} "
                  f"node-data-bg={v['dataBg']} node-offline-bg={v['offline']}")
    b.close()
