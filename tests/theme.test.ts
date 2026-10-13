/**
 * 主题门禁测试：配色对比度（WCAG）+ 场景素材闸门 + 清单配置项。
 *
 * 为什么要有这一套：上游 Komari Glass **没有测试套件**，而这类"换皮"主题最容易
 * 悄悄坏在配色上——实测踩过：只映射了暗色档与两档共用的色值，亮色档的独有色
 * 全漏 →「深玻璃卡 + 深灰字」对比度掉到 1.14（肉眼几乎看不见）。
 * 所以把"每一档的文字/底色对比度"与"素材是否齐、是否超体积"钉成断言。
 */
import { existsSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const ROOT = process.cwd();

/** 三个时段，全文件共用（describe 块内定义会作用域外不可见） */
const times = ['dusk', 'night', 'deepnight'] as const;

/* ── 1. 配色对比度：两档的正文/次要文字都要过 AA ───────────────────────── */

function hex(v: string): [number, number, number] {
  const s = v.trim().replace('#', '');
  const n = s.length === 3 ? s.split('').map((c) => c + c).join('') : s;
  return [parseInt(n.slice(0, 2), 16), parseInt(n.slice(2, 4), 16), parseInt(n.slice(4, 6), 16)];
}

/** WCAG 相对亮度 */
function luminance([r, g, b]: [number, number, number]): number {
  const f = (c: number) => {
    const x = c / 255;
    return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}

function contrast(a: string, b: string): number {
  const [l1, l2] = [luminance(hex(a)), luminance(hex(b))].sort((x, y) => y - x);
  return (l1 + 0.05) / (l2 + 0.05);
}

function blockBody(css: string, header: ':root' | '.dark'): string {
  const i = css.indexOf(`${header} {`);
  if (i < 0) return '';
  return css.slice(i, css.indexOf('\n}', i));
}

function token(body: string, name: string): string {
  const m = body.match(new RegExp(`${name}\\s*:\\s*(#[0-9a-fA-F]{3,6})`));
  return m ? m[1] : '';
}

const css = readFileSync(join(ROOT, 'src/app/globals.css'), 'utf8');

describe.each([':root', '.dark'] as const)('配色对比度 %s', (header) => {
  const body = blockBody(css, header);

  it('该档存在且关键令牌齐全', () => {
    expect(body).not.toBe('');
    for (const t of ['--background', '--foreground', '--muted-foreground', '--primary', '--node-card-bg']) {
      expect(body).toContain(t);
    }
  });

  it('正文（foreground）在背景上 ≥ 4.5:1', () => {
    expect(contrast(token(body, '--foreground'), token(body, '--background'))).toBeGreaterThanOrEqual(4.5);
  });

  it('次要文字（muted-foreground）在背景上 ≥ 4.5:1', () => {
    expect(contrast(token(body, '--muted-foreground'), token(body, '--background'))).toBeGreaterThanOrEqual(4.5);
  });

  it('强调色（primary）在背景上 ≥ 3:1（大字号/图形可用）', () => {
    expect(contrast(token(body, '--primary'), token(body, '--background'))).toBeGreaterThanOrEqual(3);
  });

  it('两档都必须是"夜色"：背景亮度不得高于 0.2（否则浅色偏好下会闪白面板）', () => {
    expect(luminance(hex(token(body, '--background')))).toBeLessThan(0.2);
  });
});

/* ── 2. 场景素材闸门 ─────────────────────────────────────────────────── */

describe('祭典街景素材', () => {
  const dir = join(ROOT, 'public/scene');

  it('恰好三张，命名与时段一一对应（多一张少一张都算不合格）', () => {
    const files = ['dusk.webp', 'night.webp', 'deepnight.webp'];
    for (const f of files) expect(existsSync(join(dir, f))).toBe(true);
    expect(files.length).toBe(times.length);
  });

  it('每张 ≤ 400KB（面板要能快速加载）', () => {
    for (const t of times) {
      const kb = statSync(join(dir, `${t}.webp`)).size / 1024;
      expect(kb, `${t}.webp 体积 ${kb.toFixed(0)}KB`).toBeLessThanOrEqual(400);
    }
  });

  it('素材带 webp 文件头（RIFF....WEBP）', () => {
    for (const t of times) {
      const buf = readFileSync(join(dir, `${t}.webp`)).subarray(0, 12);
      expect(buf.subarray(0, 4).toString('ascii')).toBe('RIFF');
      expect(buf.subarray(8, 12).toString('ascii')).toBe('WEBP');
    }
  });
});

/* ── 3. 清单配置项 ───────────────────────────────────────────────────── */

describe('主题清单', () => {
  const manifest = JSON.parse(readFileSync(join(ROOT, 'komari-theme.json'), 'utf8')) as {
    name: string;
    short: string;
    configuration?: { data?: { key: string; default?: string; options?: string }[] };
  };

  it('名字与短名已改成祭典主题', () => {
    expect(manifest.name).toBe('Komari-Matsuri');
    expect(manifest.short).toBe('Komari-Matsuri');
  });

  it('场景时段有两个配置项，且白名单/默认值合法', () => {
    const items = manifest.configuration?.data ?? [];
    const mode = items.find((i) => i.key === 'sceneTimeMode');
    const fixed = items.find((i) => i.key === 'sceneFixedTime');
    expect(mode, '缺 sceneTimeMode').toBeTruthy();
    expect(fixed, '缺 sceneFixedTime').toBeTruthy();
    expect(mode?.options?.split(',')).toEqual(['auto', 'fixed']);
    expect(mode?.default).toBe('auto');
    expect(fixed?.options?.split(',')).toEqual(times);
    expect(times).toContain(fixed?.default);
  });

  it('不应再有季节/天气这类已废弃的轴', () => {
    const keys = (manifest.configuration?.data ?? []).map((i) => i.key).join(',');
    expect(keys).not.toMatch(/season|weather/i);
  });
});
