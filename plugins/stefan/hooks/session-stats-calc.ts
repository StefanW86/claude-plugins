import type { Group, Stats } from '../types'

type Usage = {
  input_tokens: number
  output_tokens: number
  cache_read_input_tokens: number
  cache_creation_input_tokens: number
}
type Reading = { kind: string; percentUsed: number }

export const empty = (startedAt: number): Stats => ({
  startedAt,
  tokens: 0,
  cacheRead: 0,
  promptTokens: 0,
  turns: 0,
  timeMs: { main: 0, code: 0, review: 0, other: 0 },
  agents: {},
  limits: {},
  turnStartUsd: 0,
  turnCosts: [],
})

export const groupOf = (type: string | undefined): Group => {
  if (type?.endsWith('task-implementer')) return 'code'
  if (type?.endsWith('task-reviewer') || type?.endsWith('ui-walker')) return 'review'
  return 'other'
}

export const addUsage = (s: Stats, u: Usage): Stats => {
  const prompt = u.input_tokens + u.cache_read_input_tokens + u.cache_creation_input_tokens
  return {
    ...s,
    tokens: s.tokens + prompt + u.output_tokens,
    cacheRead: s.cacheRead + u.cache_read_input_tokens,
    promptTokens: s.promptTokens + prompt,
  }
}

export const addTime = (s: Stats, group: Group, ms: number, isMainTurn: boolean): Stats => ({
  ...s,
  turns: s.turns + (isMainTurn ? 1 : 0),
  timeMs: { ...s.timeMs, [group]: s.timeMs[group] + ms },
})

// Counts what a limit window grew while this session worked. `isBaseline`
// only takes the readings: what grew while idle belongs to other sessions.
// A drop means the window reset; the share starts over in the new window.
export const applyLimits = (s: Stats, readings: Reading[], isBaseline: boolean): Stats => {
  const limits = { ...s.limits }
  for (const r of readings) {
    const prev = limits[r.kind]
    const isReset = prev !== undefined && r.percentUsed < prev.percent
    const grew = prev === undefined || isBaseline || isReset ? 0 : r.percentUsed - prev.percent
    limits[r.kind] = {
      percent: r.percentUsed,
      share: (isReset ? 0 : (prev?.share ?? 0)) + grew,
    }
  }
  return { ...s, limits }
}

export const costs = (s: Stats, totalUsd: number | undefined): Record<Group, number> => {
  const out: Record<Group, number> = { main: 0, code: 0, review: 0, other: 0 }
  for (const a of Object.values(s.agents)) out[a.group] += a.usd
  out.main = Math.max(0, (totalUsd ?? 0) - out.code - out.review - out.other)
  return out
}

export const usd = (n: number) => `$${n.toFixed(2)}`

export const tokens = (n: number) =>
  n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `${Math.round(n / 1e3)}k` : `${n}`

export const duration = (ms: number) => {
  const sec = Math.round(ms / 1000)
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const ss = sec % 60
  return h > 0 ? `${h}h${String(m).padStart(2, '0')}m` : m > 0 ? `${m}m${String(ss).padStart(2, '0')}s` : `${ss}s`
}

export const percent = (n: number) => `${n.toFixed(1).replace(/\.0$/, '')}%`

const LIMIT_NAMES: Record<string, string> = { five_hour: '5h', seven_day: '7d', spend_limit: 'Budget' }
export const limitName = (kind: string) => LIMIT_NAMES[kind] ?? kind

// What each main turn cost, its subagents included; the last 12 for the curve.
export const endTurn = (s: Stats, totalUsd: number | undefined): Stats => ({
  ...s,
  turnCosts: [...s.turnCosts, Math.max(0, (totalUsd ?? 0) - s.turnStartUsd)].slice(-12),
})

const BARS = '▁▂▃▄▅▆▇█'
export const spark = (values: number[]) => {
  const max = Math.max(...values, 0)
  return values.map(v => BARS[max > 0 ? Math.round((v / max) * (BARS.length - 1)) : 0]).join('')
}
