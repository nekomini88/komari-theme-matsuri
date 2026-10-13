"""夏夜祭典（玻璃底）第 1 批：身份改名 + 配色换夜祭。

底座：imengying/Komari-Glass v1.2.7（MIT）· Next.js + React + Tailwind v4
手法：① 色值→色值映射（globals.css 两个档都换）；② 身份字段定向替换（带未命中回报）。
"""
import json
import pathlib
import re

R = pathlib.Path('/root/komari-matsuri-glass')

# ── ① 配色：色值映射（暗色档 + 亮色档都映射到"夜祭"）────────────────────────
COLOR_MAP = {
    # 主强调：青绿 → 提灯橙
    '#39c79a': '#ff9a3c', '#38c895': '#7fd4a2', '#54d6ab': '#ffb35c',
    # 语义
    '#fb7185': '#e8544d',   # destructive → 祭典红
    '#f0ad3d': '#ffd479',   # warning → 花火金
    '#69a7e8': '#7faed9',   # info → 浴衣蓝
    # 信号（图表五色）→ 祭典五色
    '#10b981': '#ff9a3c', '#4ade80': '#ffd479', '#a3e635': '#e8544d',
    '#fde047': '#7fd4a2',
    # 文字/底：冷白 → 暖白；近黑 → 夜靛
    '#f3f6f5': '#fdf6ea', '#07130f': '#241000',
    '#0d1011': '#0b0f18', '#171b1c': '#191320', '#242a2b': '#241e26',
    '#9fa9a7': '#c3b2a0',
    # 亮色档（原为浅色）→ 黄昏暖夜
    '#f8fafc': '#fdf6ea', '#f1f5f9': '#2a1f26', '#e2e8f0': '#33262d',
    '#0f172a': '#fdf6ea', '#64748b': '#c3b2a0', '#334155': '#4a3a42',
}
# 带 alpha 的玻璃色（RGB 三元组映射）
RGB_MAP = {
    '218 234 230': '255 200 140',   # border → 暖边
    '30 36 37': '32 26 24',         # glass-control → 暖暗玻璃
    '10 14 22': '22 17 26',         # node-card-bg → 暖暗玻璃
    '255 255 255': '255 190 120',   # node-card-border → 暖边
    '148 163 184': '255 200 140',   # node-data-bg
    '100 116 139': '255 200 140',
    '15 23 42': '0 0 0',            # 阴影偏黑
    '226 232 240': '255 200 140',
    '241 245 249': '38 28 32',
}

IDENT = [
    ('komari-theme-glass', 'komari-theme-matsuri'),
    ('komari-theme-Komari-Glass', 'komari-theme-Komari-Matsuri'),
    ('Komari Glass', 'Komari-Matsuri'),
    ('Komari-Matsurimorphism', 'Komari-Matsuri'),   # 防误替换
    ('"glass"', '"Komari-Matsuri"'),
    ('glass 主题', '夏夜祭典主题'),
    ('一个轻量的Komari主题。', '夏夜祭典主题 · 夜靛底 + 提灯橙 + 花火金 · 神社参道夜市街景 + 玻璃面板（基于 Komari Glass 改造）'),
]


def apply_colors(path):
    p = R / path
    if not p.exists():
        print(f'  ✗ 缺 {path}')
        return
    s0 = s = p.read_text(encoding='utf-8')
    n = 0
    for old, new in COLOR_MAP.items():
        if re.search(re.escape(old), s, re.I):
            s = re.sub(re.escape(old), new, s, flags=re.I)
            n += 1
    for old, new in RGB_MAP.items():
        if old in s:
            s = s.replace(old, new)
            n += 1
    if s != s0:
        p.write_text(s, encoding='utf-8')
    print(f'  ✓ {path}：换掉 {n} 类色值')


print('=== ① 配色 ===')
apply_colors('src/app/globals.css')

print('\n=== ② 身份改名 ===')
TARGETS = ['package.json', 'komari-theme.json', 'src/app/layout.tsx',
           'src/components/Footer.tsx', 'src/components/Header.tsx',
           'scripts/package-theme.ts', 'README.md']
for rel in TARGETS:
    p = R / rel
    if not p.exists():
        print(f'  ✗ 缺 {rel}')
        continue
    s0 = s = p.read_text(encoding='utf-8')
    for a, b in IDENT:
        s = s.replace(a, b)
    if s != s0:
        p.write_text(s, encoding='utf-8')
        print(f'  ✓ {rel}')

print('\n=== ③ 清单专项 ===')
mp = R / 'komari-theme.json'
m = json.loads(mp.read_text(encoding='utf-8'))
m['name'] = m['short'] = 'Komari-Matsuri'
m['version'] = '1.0.0'
m['url'] = 'https://github.com/nekomini88/komari-theme-matsuri'
m['author'] = 'Neko（基于 mengying 的 Komari Glass 改造 · MIT）'
cfg = m.get('configuration') or {}
if isinstance(cfg, dict):
    cfg['name'] = 'Komari-Matsuri 设置'
m['configuration'] = cfg
mp.write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('  ✓ 名字/短名/版本/仓库/作者/设置组名')

pp = R / 'package.json'
pk = json.loads(pp.read_text(encoding='utf-8'))
pk['name'] = 'komari-theme-matsuri'
pk['version'] = '1.0.0'
pp.write_text(json.dumps(pk, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('  ✓ package.json')

print('\n=== ④ 残留复核 ===')
for pat in ['glass', 'Glass', 'mengying']:
    hits = [str(f.relative_to(R)) for f in R.rglob('*')
            if f.is_file() and pat in f.name and 'node_modules' not in f.parts]
    print(f'  文件名含 {pat}: {hits[:6] or "无"}')
