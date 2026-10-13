/**
 * 时段（场景）系统 —— 只保留「时段自动切换」，不做场景选择器。
 *
 * 为什么不用访客本地时间：本站的展示口径统一以 **服务端 UTC+8** 为准。
 * 访客可能在任意时区，若用 `new Date().getHours()`，同一个深夜会出现
 * 「国内访客看到深夜、海外访客看到黄昏」的不一致。做法是拿任意 API 响应
 * 的 `Date` 头校准出「本地钟 → 服务端钟」的偏移，之后一律按服务端 UTC+8 算。
 */

export const TIMES_OF_DAY = ["dusk", "night", "deepnight"] as const;
export type TimeOfDay = (typeof TIMES_OF_DAY)[number];

export const SCENE_TIME_MODES = ["auto", "fixed"] as const;
export type SceneTimeMode = (typeof SCENE_TIME_MODES)[number];

/** 本站口径时区：UTC+8。 */
const WORLD_OFFSET_HOURS = 8;

/** 本地钟 → 服务端钟的偏移（毫秒）。未校准时为 0（即暂时按本地钟走）。 */
let serverOffsetMs = 0;

/**
 * 用 API 响应的 `Date` 头校准服务端时钟。
 * 同源请求的 Date 头可读；任何一次 rpc2 调用都能校准，失败静默忽略。
 */
export function calibrateServerClock(res: Response): void {
  const header = res.headers.get("date");
  if (!header) return;
  const parsed = Date.parse(header);
  if (!Number.isFinite(parsed)) return;
  serverOffsetMs = parsed - Date.now();
}

/** 当前的服务端 UTC+8 小时（0-23）。 */
export function worldHour(now: number = Date.now()): number {
  const shifted = new Date(now + serverOffsetMs + WORLD_OFFSET_HOURS * 3_600_000);
  return shifted.getUTCHours();
}

/**
 * 小时 → 时段。三档边界：
 *   dusk      17:00–19:59  灯初上，天边还有余光
 *   night     20:00–01:59  夜市最盛
 *   deepnight 02:00–16:59  散场后的长夜（也覆盖白天来访）
 */
export function timeOfDayFromHour(hour: number): TimeOfDay {
  const h = ((hour % 24) + 24) % 24;
  if (h >= 17 && h < 20) return "dusk";
  if (h >= 20 || h < 2) return "night";
  return "deepnight";
}

/** 时段 → 素材路径。素材在 public/scene/，静态导出后即 /scene/<时段>.webp。 */
export function sceneUrlFor(time: TimeOfDay): string {
  return `/scene/${time}.webp`;
}

/** 当前该用哪个时段：auto 跟随服务端时钟，fixed 用设置里选定的档。 */
export function resolveSceneTime(
  mode: SceneTimeMode | undefined,
  fixed: TimeOfDay | undefined,
  now: number = Date.now()
): TimeOfDay {
  if (mode === "fixed") return fixed ?? "night";
  return timeOfDayFromHour(worldHour(now));
}

export function normalizeSceneTimeMode(value: unknown): SceneTimeMode {
  return value === "fixed" ? "fixed" : "auto";
}

export function normalizeTimeOfDay(value: unknown): TimeOfDay {
  return TIMES_OF_DAY.includes(value as TimeOfDay) ? (value as TimeOfDay) : "night";
}
