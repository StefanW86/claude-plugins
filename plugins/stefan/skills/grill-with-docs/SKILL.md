---
name: grill-with-docs
description: Interviews the user relentlessly about a plan, decision, or idea until every branch is settled, then writes the plan to docs/plans/. Use when the user wants to stress-test their thinking or uses any 'grill' trigger phrases.
---

Interview the user until you share a complete understanding. Track the decisions as a **design tree** in your head (each decision branches into the ones that depend on it). Never show the tree, a question queue, or progress counters.

## Mandatory topics
Always settle these, even if the user does not raise them: **user stories**, **target platforms**, **tech stack**, **frontend**, **backend**, **API**. The user may explicitly delegate a detail; record it under "Left to the builder". For each user story probe empty states, error states, validation, concurrent edits, and performance or security needs.
- **Target platforms:** a question of its own, `multiSelect: true`, one option per device (desktop browser, iPad, iPhone, Android phone). Ask what the app is designed, built and tested for, not which device the user mostly uses, and state the consequence: unselected platforms get no design and no tests. For each selected mobile device follow up: browser, installable PWA or native app.
- **Tech stack, libraries, UI approach:** the user's other projects are one option, never the default. Always offer at least one current alternative they do not use yet (check via Context7 or the web: newer, better maintained, simpler) with trade-offs, and recommend on merit, not familiarity. Look into other projects only for what the user wants to reuse (e.g. the deploy pattern).

## Asking
- **Exactly one question per turn**, via `AskUserQuestion`, your recommendation first. At most one short line of text before the call. Plain text only if the tool is unavailable.
- Ask from the **frontier** (decisions whose prerequisites are settled) the question whose answer reshapes the most of the remaining tree.
- After each answer: record it, rebuild the tree from scratch (prune, add, rephrase; never ask something only because you planned it), then ask the next one. If the answer is vague or contradicts an earlier decision or the code, clarify that first.

## Techniques
- **Facts are your job, decisions are the user's.** Look up code, files and docs yourself (sub-agent for broad searches; keep asking other frontier questions while it runs).
- **Sharpen terms:** propose a canonical term for vague or overloaded words; collect them for the glossary.
- **Probe with scenarios:** invent concrete edge cases that force precise boundaries.

## Ending
When the frontier is empty, summarize the decisions and ask for confirmation. Only after confirmation write the plan and give its path; implementation is not part of this skill. Suggest the next step: `stefan:ui-design` if the plan needs new UI, otherwise `stefan:plan-to-spec`.

## The plan
- Path: `docs/plans/NNNN-<slug>.md`, NNNN = highest number in `docs/plans/` and `docs/specs/` + 1, zero-padded (start `0001`); the slug names the decision. Create it only when writing. Revisiting an existing plan → update it and say what changed. No repo → ask where.
- Written in the session's language for a builder who must not need to ask back. Record decisions as the user made them; for overrides, note their reason.
- Structure (drop empty sections, never the mandatory ones):

```markdown
# NNNN – <Title>

- **Status:** Accepted
- **Date:** YYYY-MM-DD

## Intent
## User stories
## Goals
## Non-goals
## Anti-goals
## Platforms
## Technology
## Constraints
## Approaches considered
## Decisions
## Glossary
## Left to the builder
```

Intent: what and why, trigger, who benefits. User stories: numbered, "As <role> I want <action> so that <benefit>". Platforms: target devices and resolutions. Technology: stack, frontend, backend, API (style, main endpoints or actions). Non-goals: deliberately out of scope. Anti-goals: what it must avoid becoming or causing. Approaches: options with trade-offs, why chosen or rejected. Decisions: each with rationale and the scenarios that settled it. Left to the builder: only points explicitly delegated; nothing silently assumed.
