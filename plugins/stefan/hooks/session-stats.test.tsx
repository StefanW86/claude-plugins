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
  let spent = 2
  on('session.usage', () => ({
    value: {
      startedAt: 0,
      context: { window: 200_000 },
      rateLimits: [{ kind: 'five_hour', percentUsed: 40 }],
      cost: { usd: spent },
    },
  }))
  on('agent.list', () => ({
    value: [{ id: 'a1', type: 'stefan:task-implementer', cost: { usd: 4 } } as unknown as AgentInfo],
  }))
  on('clock.now', () => ({ value: 3_600_000 }))
  on('turn.start', (_, e) => ({ turnId: e.turnId }))
  on('turn.complete', () => ({ text: '' }))

  await $.turn.start({ text: 'los', turnId: 't1' })
  spent = 10
  await $.turn.complete({
    answer: '', durationMs: 120_000, isAborted: false, turnId: 's1', agentId: 'a1', reason: 'answer',
  })
  await $.turn.complete({
    answer: '', durationMs: 300_000, isAborted: false, turnId: 't1', reason: 'answer',
  })

  for (const surface of ['terminal', 'desktop', 'vscode', 'mobile'] as const) {
    const ui = await $.ui.mount({ ...BAND, surface })
    const text = async (t: RegExp) => (await ui.find({ type: 'Text', text: t }))?.text
    expect(await text(/^Kosten/)).toBe('Kosten (Schätzung)')
    expect(await text(/^\$10/)).toBe('$10.00')
    expect(await text(/^letzter/)).toBe('letzter $8.00 · Haupt $6.00')
    expect(await text(/^Ø/)).toBe('Ø 5m00s / Turn')
    expect(await text(/^Zeit 2m/)).toBe('Zeit 2m00s')
    expect(await text(/^Limit/)).toBe('Limit 5h')
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

test('Subagent-Kosten und -Zeit zählen, auch wenn der Agent am Ende nicht mehr gelistet ist', async ($, on) => {
  let listed = [{ id: 'a1', type: 'stefan:task-implementer', cost: { usd: 3 } } as unknown as AgentInfo]
  on('session.usage', () => ({
    value: { startedAt: 0, context: { window: 200_000 }, rateLimits: [], cost: { usd: 10 } },
  }))
  on('agent.list', () => ({ value: listed }))
  on('session.surfaces', () => ({ value: [] }))
  on('clock.now', () => ({ value: 600_000 }))
  on('turn.start', (_, e) => ({ turnId: e.turnId }))
  on('turn.step', async function* (_, e) {
    return { turnId: e.turnId, index: e.index, answer: '', toolUses: [] } as never
  })
  on('turn.complete', () => ({ text: '' }))
  on('command.run', () => ({ text: '' }))

  await $.turn.start({ text: 'los', turnId: 't1' })
  const step = $.turn.step({ turnId: 's1', index: 0, model: 'sonnet', messageCount: 1, agentId: 'a1' })
  for await (const _ of step) {
    // Chunks interessieren hier nicht.
  }
  listed = []
  await $.turn.complete({
    answer: '', durationMs: 60_000, isAborted: false, turnId: 's1', agentId: 'a1', reason: 'answer',
  })
  await $.turn.complete({ answer: '', durationMs: 120_000, isAborted: false, turnId: 't1', reason: 'answer' })

  const r = await $.command.run({
    command: 'stefan:session-stats',
    args: '',
    origin: { kind: 'composer' },
    presentation: { isFullscreen: false, columns: 120 },
  })
  expect(r.text).toContain('Kosten  Haupt $7.00 · Code $3.00')
  expect(r.text).toContain('Code 1m00s')
})
