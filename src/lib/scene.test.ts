import { describe, expect, it } from 'vitest';

import {
  TIMES_OF_DAY,
  calibrateServerClock,
  normalizeSceneTimeMode,
  normalizeTimeOfDay,
  resolveSceneTime,
  sceneUrlFor,
  timeOfDayFromHour,
  worldHour,
} from './scene';

describe('时段系统', () => {
  it('只有三档，且顺序为 黄昏 → 夜 → 深夜', () => {
    expect(TIMES_OF_DAY).toEqual(['dusk', 'night', 'deepnight']);
  });

  it('小时→时段 的边界：黄昏 17-19、夜 20-1、深夜 2-16', () => {
    expect(timeOfDayFromHour(16)).toBe('deepnight');
    expect(timeOfDayFromHour(17)).toBe('dusk');
    expect(timeOfDayFromHour(19)).toBe('dusk');
    expect(timeOfDayFromHour(20)).toBe('night');
    expect(timeOfDayFromHour(23)).toBe('night');
    expect(timeOfDayFromHour(0)).toBe('night');
    expect(timeOfDayFromHour(1)).toBe('night');
    expect(timeOfDayFromHour(2)).toBe('deepnight');
    expect(timeOfDayFromHour(12)).toBe('deepnight');
  });

  it('越界小时取模，不会抛错', () => {
    expect(timeOfDayFromHour(25)).toBe('night');
    expect(timeOfDayFromHour(-1)).toBe('night');
  });

  it('素材路径与时段一一对应', () => {
    expect(sceneUrlFor('dusk')).toBe('/scene/dusk.webp');
    expect(sceneUrlFor('night')).toBe('/scene/night.webp');
    expect(sceneUrlFor('deepnight')).toBe('/scene/deepnight.webp');
  });

  it('auto 跟随服务端钟；fixed 用选定档', () => {
    // 2026-10-14T03:00:00Z → UTC+8 = 11:00 → 深夜
    const t = Date.parse('2026-10-14T03:00:00Z');
    expect(resolveSceneTime('auto', 'dusk', t)).toBe('deepnight');
    expect(resolveSceneTime('fixed', 'dusk', t)).toBe('dusk');
    expect(resolveSceneTime('fixed', 'night', t)).toBe('night');
  });

  it('设置归一化：非法值一律回落到默认（auto / night）', () => {
    expect(normalizeSceneTimeMode('fixed')).toBe('fixed');
    expect(normalizeSceneTimeMode('FIXED')).toBe('auto');
    expect(normalizeSceneTimeMode(undefined)).toBe('auto');
    expect(normalizeTimeOfDay('dusk')).toBe('dusk');
    expect(normalizeTimeOfDay('noon')).toBe('night');
    expect(normalizeTimeOfDay(undefined)).toBe('night');
  });
});

describe('服务端时钟校准', () => {
  it('从响应 Date 头算出偏移，worldHour 按 UTC+8 走', () => {
    // 构造一个"服务端时间 = 本地 + 8 小时"的响应
    const fakeNow = Date.now();
    const serverDate = new Date(fakeNow + 8 * 3_600_000).toUTCString();
    const fakeRes = { headers: { get: (k: string) => (k === 'date' ? serverDate : null) } } as unknown as Response;
    calibrateServerClock(fakeRes);

    // 本地此刻若是 X 点，worldHour 应该读出 (X + 8 + 8) % 24
    const expected = new Date(fakeNow + 16 * 3_600_000).getUTCHours();
    expect(Math.abs(worldHour(fakeNow) - expected)).toBeLessThanOrEqual(1);
  });

  it('没有 Date 头或头非法时不抛错、不改变行为', () => {
    const noHeader = { headers: { get: () => null } } as unknown as Response;
    expect(() => calibrateServerClock(noHeader)).not.toThrow();
    const badHeader = { headers: { get: () => 'not-a-date' } } as unknown as Response;
    expect(() => calibrateServerClock(badHeader)).not.toThrow();
  });
});
