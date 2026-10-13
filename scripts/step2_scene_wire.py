"""夏夜祭典（玻璃底）第 2 批：接上祭典街景 + 时段自动切换。

优先级：用户在设置里填的 backgroundImage > 内置祭典街景（按时段自动换）。
时段跟随 **服务端 UTC+8**（从 API 响应 Date 头校准），不跟随访客本地钟。
"""
import json
import pathlib

R = pathlib.Path('/root/komari-matsuri-glass')
miss: list[str] = []


def sub(rel: str, old: str, new: str, count: int = 1) -> None:
    p = R / rel
    s = p.read_text(encoding='utf-8')
    if old not in s:
        miss.append(f'{rel}: 未命中 -> {old[:70]}')
        return
    p.write_text(s.replace(old, new, count), encoding='utf-8')
    print(f'  ✓ {rel}')


print('=== ① types.ts：加两个设置字段 ===')
sub('src/lib/types.ts',
    '  backgroundImage?: string;\n',
    '  backgroundImage?: string;\n'
    '  /** 场景时段：auto=跟随服务端时钟自动切换，fixed=固定为选定档 */\n'
    '  sceneTimeMode?: "auto" | "fixed";\n'
    '  /** 固定时段（仅 sceneTimeMode=fixed 时生效） */\n'
    '  sceneFixedTime?: "dusk" | "night" | "deepnight";\n')

print('\n=== ② theme-settings.ts：默认值 + 合并 + 归一化 ===')
sub('src/lib/theme-settings.ts',
    'import {\n  ASSET_CURRENCIES,',
    'import {\n  normalizeSceneTimeMode,\n  normalizeTimeOfDay,\n} from "./scene";\nimport {\n  ASSET_CURRENCIES,')
sub('src/lib/theme-settings.ts',
    '    | "backgroundImage"\n',
    '    | "backgroundImage"\n    | "sceneTimeMode"\n    | "sceneFixedTime"\n')
sub('src/lib/theme-settings.ts',
    '  backgroundImage: "",\n',
    '  backgroundImage: "",\n  sceneTimeMode: "auto",\n  sceneFixedTime: "night",\n')
sub('src/lib/theme-settings.ts',
    '    backgroundImage: String(\n      src.backgroundImage ?? DEFAULT_THEME_SETTINGS.backgroundImage\n    ),',
    '    backgroundImage: String(\n      src.backgroundImage ?? DEFAULT_THEME_SETTINGS.backgroundImage\n    ),\n'
    '    sceneTimeMode: normalizeSceneTimeMode(src.sceneTimeMode),\n'
    '    sceneFixedTime: normalizeTimeOfDay(src.sceneFixedTime),')

print('\n=== ③ api.ts：每次 rpc2 调用顺手校准服务端钟 ===')
sub('src/lib/api.ts',
    'import ',
    'import { calibrateServerClock } from "./scene";\nimport ', 1)
sub('src/lib/api.ts',
    '  if (!res.ok) {\n    throw new Error(`请求失败 (${res.status})`);\n  }',
    '  // 顺手用响应头校准服务端时钟：场景时段按服务端 UTC+8 算，而不是访客本地钟。\n'
    '  calibrateServerClock(res);\n'
    '  if (!res.ok) {\n    throw new Error(`请求失败 (${res.status})`);\n  }')

print('\n=== ④ AppProvider.tsx：背景 = 街景（按时段）+ 定时重算 ===')
sub('src/contexts/AppProvider.tsx',
    'import { getLiveWebSocket } from "@/lib/websocket";',
    'import { resolveSceneTime, sceneUrlFor } from "@/lib/scene";\n'
    'import { getLiveWebSocket } from "@/lib/websocket";')
sub('src/contexts/AppProvider.tsx',
    '  const [systemDark, setSystemDark] = useState(false);',
    '  const [systemDark, setSystemDark] = useState(false);\n'
    '  // 时段每 60s 重算：跨过档位边界时自动换街景，访客无需刷新。\n'
    '  const [clockNow, setClockNow] = useState(() => Date.now());')
sub('src/contexts/AppProvider.tsx',
    '    const bg = resolveBackground(settings.backgroundImage, resolvedTheme === "dark");',
    '    // 背景优先级：设置里填的自定义图 > 内置祭典街景（按时段自动切换）。\n'
    '    const sceneTime = resolveSceneTime(settings.sceneTimeMode, settings.sceneFixedTime, clockNow);\n'
    '    const custom = settings.backgroundImage.trim();\n'
    '    const bg = custom\n'
    '      ? resolveBackground(custom, resolvedTheme === "dark")\n'
    '      : sceneUrlFor(sceneTime);')
sub('src/contexts/AppProvider.tsx',
    '    root.dataset.blur = settings.enableBlur ? "on" : "off";\n  }, [resolvedTheme, settings.backgroundImage, settings.enableBlur]);',
    '    root.dataset.time = sceneTime;\n'
    '    root.dataset.blur = settings.enableBlur ? "on" : "off";\n'
    '  }, [\n    resolvedTheme,\n    settings.backgroundImage,\n    settings.enableBlur,\n'
    '    settings.sceneTimeMode,\n    settings.sceneFixedTime,\n    clockNow,\n  ]);\n\n'
    '  useEffect(() => {\n'
    '    const timer = window.setInterval(() => setClockNow(Date.now()), 60_000);\n'
    '    return () => window.clearInterval(timer);\n'
    '  }, []);')

print('\n=== ⑤ 清单：加两个配置项 ===')
mp = R / 'komari-theme.json'
m = json.loads(mp.read_text(encoding='utf-8'))
cfg = m.get('configuration') or {}
items = cfg.get('data') if isinstance(cfg.get('data'), list) else None
if items is None:
    print('  ! configuration.data 不是列表，结构需人工确认：', list(cfg.keys()) if isinstance(cfg, dict) else type(cfg))
else:
    items = [i for i in items if i.get('key') not in ('sceneTimeMode', 'sceneFixedTime')]
    items.append({
        'name': '场景世界（时段）', 'key': 'sceneTimeMode', 'type': 'select',
        'default': 'auto', 'options': 'auto,fixed',
        'help': 'auto = 跟随服务端时间（UTC+8）自动切换；fixed = 固定为下面选定的时段',
    })
    items.append({
        'name': '固定时段', 'key': 'sceneFixedTime', 'type': 'select',
        'default': 'night', 'options': 'dusk,night,deepnight',
        'help': '仅当「时间来源」选 fixed 时生效：dusk=黄昏（灯初上）、night=夜（最盛）、deepnight=深夜（散场后）',
    })
    cfg['data'] = items
    m['configuration'] = cfg
    mp.write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'  ✓ 配置项共 {len(items)} 项，末两项为场景时段')

print('\n=== ⑥ 未命中清单 ===')
print('  ' + ('\n  '.join(miss) if miss else '无 ✓ 全部命中'))
