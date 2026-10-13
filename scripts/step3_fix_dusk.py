"""修根因：亮色档（:root）**整块**重写为一致的「黄昏夜」。

上一轮的教训：值→值映射只覆盖了暗色档与两档共用的色，亮色档的**独有色值全漏**
（#0f766e / #11191f / #59666f / #edf1f3 …）→ 结果是「深玻璃卡 + 深灰字」= 对比度 1.14。
教训记在技能里：**改一档就要整块改，不要只映射共用色**。

本档设计：黄昏（灯初上）——底比深夜档略暖略亮，字/强调与深夜档同一体系，
保证访客在「浅色偏好」下看到的也是夜色，而不是白面板。
"""
import pathlib
import re

p = pathlib.Path('/root/komari-matsuri-glass/src/app/globals.css')
s = p.read_text(encoding='utf-8')

DUSK = """:root {
  /* 黄昏档（原上游亮色档）：整块重写，保证与本主题其它档同体系。
     底/面为暗，字/强调为暖亮 —— 与深夜档一致，只把夜色调得更暖更浅一档。 */
  --background: #1a1420;
  --foreground: #fdf6ea;
  --card-solid: #211a29;
  --card-foreground: #fdf6ea;
  --primary: #ff9a3c;
  --primary-foreground: #241000;
  --muted: #2a2231;
  --muted-foreground: #c3b2a0;
  --destructive: #e8544d;
  --warning: #ffd479;
  --success: #7fd4a2;
  --info: #7faed9;
  --selection: #ffb35c;
  --border: rgb(255 200 140 / 0.16);
  --ring: #ff9a3c;
  --signal-1: #ff9a3c;
  --signal-2: #ffd479;
  --signal-3: #e8544d;
  --signal-4: #7fd4a2;
  --signal-5: #a99bf0;
  --glass-shadow: 0 10px 32px rgb(0 0 0 / 0.34),
    inset 0 1px 0 rgb(255 190 120 / 0.10);
  --glass-control: rgb(38 28 34 / 0.82);
  --node-card-bg: rgb(38 28 32 / 0.74);
  --node-card-hover: rgb(46 34 38 / 0.82);
  --node-card-border: rgb(255 200 140 / 0.20);
  --node-card-shadow: 0 8px 28px rgb(0 0 0 / 0.42);
  --node-data-bg: rgb(255 200 140 / 0.07);
  --node-offline-bg: rgb(0 0 0 / 0.22);
}"""

new, n = re.subn(r':root\s*\{.*?\n\}', DUSK, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f'✗ :root 块替换失败（匹配 {n} 处）')
p.write_text(new, encoding='utf-8')
print('  ✓ 亮色档整块重写为「黄昏」')

# 复核：两档里是否还有上游遗留的色值（说明又漏了）
import subprocess
for header in (':root', '.dark'):
    m = re.search(re.escape(header) + r'\s*\{(.*?)\n\}', new, re.S)
    body = m.group(1) if m else ''
    left = sorted({c for c in re.findall(r'#[0-9a-fA-F]{6}', body)})
    print(f'  {header} 现有色值: {", ".join(left)}')
