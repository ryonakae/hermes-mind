---
name: hermes-mind-provider-development
description: Use when developing Hermes mind providers. Verify APIs.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, memory, plugins, mind, profile-isolation, testing]
---

# Thin Hermes mind provider workflow

## When to Use

Use this skill when implementing or reviewing a user-installed Hermes memory provider that wraps the local `mind` artifact.

- Inspect the active Hermes runtime before coding: resolve `hermes`, `sys.executable`, `agent.memory_provider`, `plugins.memory`, and the live config. Do not assume a copied source checkout is the running runtime.
- Use the public `MemoryProvider` seam and `register(ctx)`. Keep built-in `MEMORY.md` / `USER.md` and LCM additive; do not replace or import them.
- Pin the upstream single-file mind artifact by stable tag, peeled commit, and SHA-256. The user prefers explicit setup-time download rather than tracking upstream source in Git. Keep `vendor/mind.py` ignored and locally available; `setup_mind.py` fetches the pinned commit, validates SHA-256 before replacing the file, and skips downloads when already valid. Never download at runtime or patch upstream algorithms. Exercise real download in an isolated scratch directory as well as failure/idempotence tests.
- When the artifact should not be tracked, put the fixed URL/commit/SHA in a small stdlib-only setup script; stream into a same-directory temporary file, verify the SHA before atomic replacement, make the exact artifact path ignored, never download during provider initialization, and expose the setup command in `unavailable_reason`. Test hash/network failure preservation, idempotence, and one real isolated download.
- Prefer `initialize(..., hermes_home=...)` as the profile root. Fall back to `get_hermes_home()` only for test/runtime compatibility. Run mind commands with an explicit profile-local cwd, HOME, and `MIND_USER_HOME`; never use the process cwd or real `~/.mind`.
- If initialization is required, run upstream `mind init` only in the dedicated profile data directory, never in the home directory or an existing repository.
- Keep the integration thin: use a static trusted system policy and bounded untrusted JSON snapshots through `prefetch`. The approved periodic refresh is 30 completed user/assistant exchanges or two hours, delivered on the next substantive user message; successful mutations arm the next refresh. `sync_turn` counts completed exchanges only; `queue_prefetch` stays a no-op. Do not add automatic extraction, extra LLM calls, or background timers.
- Inspect the core replay contract before claiming prefetch is transient: Hermes can persist injected context in historical `api_content` sidecars. The accepted design bounds frequency and size rather than removing those copies. Label refreshed snapshots as current, but do not interpret absence from a top-six selection as proof of forgetting. Trivial-message suppression and asynchronous `sync_turn` mean delivery timing is approximate.
- For this provider, use the approved snapshot ceiling of six records / 1024 Hermes-estimated tokens including framing, not a fill target. When raising a token budget, also check per-record and whole-block character ceilings and the combined schema-plus-refresh test budget. Test substantial Japanese records and long English records so small independent character caps cannot silently defeat the change.
- Expose only the approved explicit actions. Validate inputs, use argv lists with `shell=False`, `stdin=DEVNULL`, bounded timeouts, and JSON-safe bounded tool results. Disable writes outside the primary agent context.
- Let upstream mind own deterministic dream scheduling when approved; do not add a second scheduler unless the design explicitly requires one.
- Test with the actual Hermes runtime Python and a temporary profile root: lifecycle, complete refresh bounds including labels/nudge, static policy separation, 30-exchange/two-hour boundaries, mutation refresh, no tool-loop counting, failure recovery, explicit actions, profile isolation, artifact hash failure, and discovery without activation.
- Run an independent read-only reviewer after substantive fixes. If Codex/OpenCode lacks authentication, use another authenticated CLI if available and report any review limitation rather than fabricating approval.
- Keep review-driven fixes minimal: reproduce the issue, guard concrete adapter-used paths, and prefer standard JSON quoting over custom filters. Do not add recursive security frameworks or claim quoted memory guarantees model compliance. The user explicitly prefers a simple thin adapter.
- Activate through `hermes config set memory.provider hermes-mind`, then verify `hermes memory status` and a fresh provider initialization with the active runtime. Distinguish that verification from adoption by the already-running gateway; ask the user to run `hermes-gateway restart` or `/restart-gateway`, never restart it from the agent.
