export type Group = 'main' | 'code' | 'review' | 'other'

export type LimitShare = { percent: number; share: number }

export type Stats = {
  startedAt: number
  tokens: number
  cacheRead: number
  promptTokens: number
  turns: number
  timeMs: Record<Group, number>
  agents: Record<string, { group: Group; usd: number }>
  limits: Record<string, LimitShare>
}

declare module 'claude-code' {
  interface PluginState {
    stefan: { stats: Shaped<Stats> }
  }
}
