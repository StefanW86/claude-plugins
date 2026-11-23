import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Group } from '../types'
import {
  addTime,
  addUsage,
  applyLimits,
  costs,
  duration,
  empty,
  groupOf,
  limitName,
  percent,
  tokens,
  usd,
} from './session-stats-calc'

// Change the tag when Stats changes: it declines what an older version stored.
const stats = atom({ plugin: 'stefan', key: 'stats' } as const, empty(0), {
  shape: 'stats-1',
})

const COMMAND = 'stefan:session-stats'

const LABELS: Record<Group, string> = { main: 'Haupt', code: 'Code', review: 'Review', other: 'Sonst.' }

// Notes each subagent the engine still lists: its group and what it cost so far.
const recordAgents = async ($: EngineInterface) => {
  const agents = await $.agent.list()
  await update($, stats, s => {
    const known = { ...s.agents }
    for (const a of agents) {
      known[a.id] = { group: groupOf(a.type), usd: a.cost?.usd ?? known[a.id]?.usd ?? 0 }
    }
    return { ...s, agents: known }
  })
}

// The figures as text lines, for the band and for /session-stats alike.
const lines = async ($: EngineInterface): Promise<string[]> => {
  const s = await read($, stats)
  const usage = await $.session.usage()
  const now = await $.clock.now()
  const cost = costs(s, usage.cost?.usd)
  const sub: Group[] = ['code', 'review', 'other']
  const reuse = s.promptTokens > 0 ? (100 * s.cacheRead) / s.promptTokens : 0
  const avg = s.turns > 0 ? s.timeMs.main / s.turns : 0
  const limits = usage.rateLimits.map(r => {
    const share = s.limits[r.kind]?.share ?? 0
    return `${limitName(r.kind)} ${percent(r.percentUsed)} (Session +${percent(share)})`
  })
  return [
    `≈${usd(usage.cost?.usd ?? 0)} (Schätzung) · ${tokens(s.tokens)} Tokens · ${s.turns} Turns · ` +
      `Agent ${duration(s.timeMs.main)} (Ø ${duration(avg)}/Turn) · ` +
      `Session ${duration(now - usage.startedAt)} · Cache ${percent(reuse)}`,
    `Kosten  ${(['main', ...sub] as Group[]).map(g => `${LABELS[g]} ${usd(cost[g])}`).join(' · ')}`,
    `Zeit    Turns ${duration(s.timeMs.main)}, davon Subagenten: ` +
      sub.map(g => `${LABELS[g]} ${duration(s.timeMs[g])}`).join(' · '),
    ...(limits.length > 0 ? [`Limits  ${limits.join(' · ')}`] : []),
  ]
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    $.clock.every(30_000, () => $.ui.invalidate('ui.render'))
    return next(e)
  })

  on('turn.start', async ($, e, next) => {
    if (e.agentId === undefined) {
      const usage = await $.session.usage()
      // A /clear starts the session's figures over.
      await update($, stats, s =>
        applyLimits(s.startedAt === usage.startedAt ? s : empty(usage.startedAt), usage.rateLimits, true),
      )
    }
    return next(e)
  })

  on('turn.step', async function* ($, e, next) {
    const step = yield* next(e)
    const usage = step.usage
    if (usage) await update($, stats, s => addUsage(s, usage))
    return step
  })

  on('turn.complete', async ($, e, next) => {
    await recordAgents($)
    const usage = await $.session.usage()
    const isMain = e.agentId === undefined
    await update($, stats, s => {
      const group = isMain ? 'main' : (s.agents[e.agentId ?? '']?.group ?? 'other')
      return applyLimits(addTime(s, group, e.durationMs, isMain), usage.rateLimits, false)
    })
    return next(e)
  })

  // commands/session-stats.md legt /stefan:session-stats an; die Mod beantwortet
  // ihn selbst. Mod-Befehle dürfen keinen Doppelpunkt im Namen tragen.
  on('command.run', async ($, e, next) => {
    const isOurs = e.command === COMMAND
    const surfaces = isOurs ? await $.session.surfaces() : []
    const text = isOurs ? (await lines($)).join('\n') : ''
    return isOurs ? { text: `${text}\n(Oberflächen: ${surfaces.join(', ') || 'keine'})` } : next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const s = await read($, stats)
    if (e.props.hasSurvey || s.turns === 0) {
      return next(e)
    }
    const { Box, Text } = $.ui.resolve(e)
    const rows = await lines($)

    return (
      <Box flexDirection="column">
        {rows.map(row => (
          <Text dimColor>{row}</Text>
        ))}
      </Box>
    )
  })
}
