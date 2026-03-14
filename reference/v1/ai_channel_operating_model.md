# AI Channel Operating Model

Assessment date: March 10, 2026

## Goal

Use Codex and Claude together without duplicating work, conflicting edits, or letting both tools invent architecture independently.

## Division of Labor

### Use Claude for divergence

Claude is best used for:

- alternative product architectures
- simplification passes on the problem statement
- UX and user-flow critique
- challenge sessions such as "what are we missing?"
- comparing 2-3 ways to scope the MVP

Best prompt style for Claude:

- give the PRD or wrap doc
- ask for 2-3 sharply different architectures
- force tradeoffs and explicit exclusions
- ask it to reduce complexity, not add features

### Use Codex for convergence

Codex is best used for:

- grounding decisions in the actual repository
- extracting contracts from real code
- writing package maps and migration plans
- implementing code
- running tests, reading failures, and tightening behavior
- reviewing whether a proposed architecture is buildable

Best prompt style for Codex:

- point to the exact files or docs in this repo
- ask for a package plan, contract extraction, or implementation
- ask for verification, not brainstorming, when code exists

## Working Loop

Use this loop during the rebuild:

1. Ask Claude for 2-3 V2 architectures from the PRD and the V1 wrap.
2. Bring the preferred option to Codex.
3. Ask Codex to pressure-test it against the current code, data, and interfaces.
4. Send Codex's package plan back to Claude for simplification or criticism.
5. Choose one direction.
6. Use Codex to execute that direction in code.

This loop keeps Claude generating options and Codex turning one option into something rigorous.

## Editing Rule

Only one agent should edit code at a time.

Do not let both channels make repository changes in parallel. The current project has no meaningful commit history yet, so parallel editing will create confusion faster than it creates velocity.

Recommended operating rule:

- Claude proposes
- Codex implements

If Claude produces code, treat it as draft input for Codex review rather than copying it directly into the repository.

## Best Task Split

### Send to Claude

- "Give me three clean V2 package architectures for this product."
- "What should be cut from MVP?"
- "Is this workflow too agentic?"
- "What are the minimum decision states for underwriting?"
- "Rewrite this package map to be simpler."

### Send to Codex

- "Extract the domain model from V1."
- "Turn this architecture into a package skeleton."
- "Implement package A and its tests."
- "Compare proposed API contracts to current routes."
- "Review this branch for regressions."

## What Not To Do

- Do not ask both tools to independently design the whole system and then merge outputs manually.
- Do not ask Claude and Codex to both write production code in the same area.
- Do not use V1 code structure as a silent default when evaluating V2.
- Do not start implementation before the package map and boundary rules are explicit.

## Suggested Prompt Sequence For The Rebuild

1. Claude:
   "Using `docs/v1_reference_wrap.md` and the PRD, propose three V2 package architectures. Keep only MVP-critical packages. Explicitly say what is excluded."

2. Codex:
   "Take option 2 and turn it into a concrete package map, domain contract list, and migration plan. Do not implement code yet."

3. Claude:
   "Critique this package map. Where is it still too broken down or too coupled?"

4. Codex:
   "Revise the package map and then scaffold the repository."

## Bottom Line

Claude should widen the search space. Codex should narrow it, anchor it to the repo, and execute it. That is the cleanest way to get the strengths of both tools without paying the usual multi-agent coordination tax.
