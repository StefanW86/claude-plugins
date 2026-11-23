import type { AgentInfo } from 'claude-code'
import { expect, test } from 'claude-code/testing'

import { applyLimits, costs, duration, empty, groupOf } from './session-stats-calc'

const BAND = {
  plugin: 'stefan',
  component: 'AbovePrompt',
  props: {
    hasSurvey: false,
    isCollapsed: false,
    isWorking: false,
    maxRows: 10,
    bodyColumns: 120,
    scroll: { offset: 0, bodyRows: 10 },
    view: {},
  },
} as const

test('ordnet Subagent-Typen den Gruppen zu', async () => {
  expect(groupOf('stefan:task-implementer')).toBe('code')
  expect(groupOf('stefan:task-reviewer')).toBe('review')
  expect(groupOf('stefan:ui-walker')).toBe('review')
  expect(groupOf('Explore')).toBe('other')
  expect(groupOf(undefined)).toBe('other')
})

test('Limit-Anteil zählt nur Zuwachs während der Arbeit, Reset beginnt neu', async () => {
  let s = applyLimits(empty(0), [{ kind: 'five_hour', percentUsed: 40 }], true)
  s = applyLimits(s, [{ kind: 'five_hour', percentUsed: 43.5 }], false)
  s = applyLimits(s, [{ kind: 'five_hour', percentUsed: 50 }], true)
  s = applyLimits(s, [{ kind: 'five_hour', percentUsed: 51 }], false)
  expect(s.limits.five_hour).toEqual({ percent: 51, share: 4.5 })
  s = applyLimits(s, [{ kind: 'five_hour', percentUsed: 2 }], false)
  expect(s.limits.five_hour).toEqual({ percent: 2, share: 0 })
})

test('Hauptkosten sind Gesamtkosten minus Subagenten', async () => {
  const s = { ...empty(0), agents: { a: { group: 'code', usd: 4 }, b: { group: 'review', usd: 1.5 } } } as const
  expect(costs({ ...s, agents: { ...s.agents } }, 10)).toEqual({ main: 4.5, code: 4, review: 1.5, other: 0 })
})

test('Dauer wird lesbar formatiert', async () => {
  expect(duration(42_000)).toBe('42s')
  expect(duration(192_000)).toBe('3m12s')
  expect(duration(4_320_000)).toBe('1h12m')
})

test('Zeile zeigt Kosten und Zeiten nach Gruppe, auf jeder Oberfläche', async ($, on) => {
  on('session.usage', () => ({
    value: {
      startedAt: 0,
      context: { window: 200_000 },
      rateLimits: [{ kind: 'five_hour', percentUsed: 40 }],
      cost: { usd: 10 },
    },
  }))
  on('agent.list', () => ({
    value: [{ id: 'a1', type: 'stefan:task-implementer', cost: { usd: 4 } } as unknown as AgentInfo],
  }))
  on('clock.now', () => ({ value: 3_600_000 }))
  on('turn.start', (_, e) => ({ turnId: e.turnId }))
  on('turn.complete', () => ({ text: '' }))

  await $.turn.start({ text: 'los', turnId: 't1' })
  await $.turn.complete({
    answer: '', durationMs: 120_000, isAborted: false, turnId: 's1', agentId: 'a1', reason: 'answer',
  })
  await $.turn.complete({
    answer: '', durationMs: 300_000, isAborted: false, turnId: 't1', reason: 'answer',
  })

  for (const surface of ['terminal', 'desktop', 'vscode', 'mobile'] as const) {
    const ui = await $.ui.mount({ ...BAND, surface })
    expect((await ui.find({ type: 'Text', text: /^Kosten/ }))?.text).toBe(
      'Kosten  Haupt $6.00 · Code $4.00 · Review $0.00 · Sonst. $0.00',
    )
    expect((await ui.find({ type: 'Text', text: /^Zeit/ }))?.text).toBe(
      'Zeit    Turns 5m00s, davon Subagenten: Code 2m00s · Review 0s · Sonst. 0s',
    )
    expect((await ui.find({ type: 'Text', text: /^Limits/ }))?.text).toBe('Limits  5h 40% (Session +0%)')
    await ui.unmount()
  }
})

for (const command of ['stefan:session-stats']) test(`/${command} gibt die Werte als Text aus`, async ($, on) => {
  on('session.usage', () => ({
    value: { startedAt: 0, context: { window: 200_000 }, rateLimits: [], cost: { usd: 1 } },
  }))
  on('session.surfaces', () => ({ value: [] }))
  on('clock.now', () => ({ value: 60_000 }))
  on('command.run', () => ({ text: '' }))

  const r = await $.command.run({
    command,
    args: '',
    origin: { kind: 'composer' },
    presentation: { isFullscreen: false, columns: 120 },
  })
  expect(r.text).toContain('Kosten  Haupt $1.00')
  expect(r.text).toContain('(Oberflächen: keine)')
})
