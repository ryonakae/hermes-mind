# hermes-mind

Thin Hermes memory-provider plugin around the pinned `mind` 7.0.0 single-file artifact.

## Scope

- **Startup only:** injects a short cached snapshot from `mind context --json`.
- **Explicit actions only:** one compact `mind` tool with `store`, `search`, `correct`, `forget`, and `confirm` actions.
- **No per-turn automatic search, extraction, or bulk history import.** `prefetch`, `queue_prefetch`, and `sync_turn` are no-ops.
- **Writes only in the `primary` agent context.** Cron, subagent, and flush contexts do not initialize or mutate a missing store.
- **Upstream maintenance stays native:** primary writes retain `MIND_AUTO_DREAM=1`. During provider initialization, the adapter checks mind's native `scheduler.json` due signal and may run one real `mind dream` when pending work is stale or reaches ten signals. A single profile-local timestamp prevents repeating the same no-write maintenance attempt; this is activity-triggered, not a background scheduler or periodic promise.
- Hermes built-in `MEMORY.md` / `USER.md` and LCM remain separate and unchanged. Selecting this provider is additive, not a replacement.

## Upstream provenance and license

`setup_mind.py` is the only download path. It fetches `mind.py` from upstream
`Da7-Tech/mind` tag `v7.0.0` at peeled commit
`ade5b2a20e37773e2ae58640b13b59840b739177`:

```text
https://raw.githubusercontent.com/Da7-Tech/mind/ade5b2a20e37773e2ae58640b13b59840b739177/mind.py
```

The pinned SHA-256 is:

```text
ae2fc389b3b09c93cb432ab55b71063d98b400da6b18d6bc178322bc8f3fcf69
```

The setup script downloads to a temporary file, verifies this SHA-256, and then
atomically replaces the destination. Hash or network failure leaves an existing
artifact unchanged. Re-running setup when the destination already has this hash
is a no-op. Runtime provider initialization never downloads anything; it only
checks the local artifact and reports the setup command when it is missing or
modified. The provider uses the active Hermes runtime's `sys.executable` and
does not install a package or require another model/API/embedding backend.

The fetched `mind.py` is copyright (c) 2026 Da7-Tech and MIT licensed. The
repository keeps the upstream attribution and license text in `LICENSE`.

## Installation

After placing this repository at `$HERMES_HOME/plugins/hermes-mind`, run the
explicit setup step from this directory:

```bash
"$HERMES_PYTHON" setup_mind.py
```

Set `HERMES_PYTHON` to the active Hermes runtime Python first. `python3 setup_mind.py` is also sufficient when that interpreter is the active runtime.
The destination defaults to `vendor/mind.py`; use `--destination PATH` for an
isolated or alternate checkout. The artifact is intentionally ignored by git,
so setup is required on a fresh clone. If setup has not been run, provider
status reports the exact command to run; there is no automatic runtime fetch.

## Profile-safe state

When activated, state is created lazily under the **profile-global** path:

```text
$HERMES_HOME/mind/.mind/
```

This is not a project-directory store despite upstream `mind` calling its root a project. `$HERMES_HOME` is resolved by Hermes, so named profiles remain isolated and the process working directory is never used. The adapter does not resolve the mind path through symlinks: it rejects symlinks at the mind root, `.mind`, `user`, and the graph/scheduler/maintenance files it reads before initialization, subprocesses, or direct reads. This is a narrow path check, not a recursive or race-proof filesystem sandbox; it assumes a trusted same-user filesystem. The first primary activation runs upstream `mind init` only in that dedicated profile directory. Non-primary initialization is read-only and does not create it.

The startup snapshot is cache-stable across Hermes `on_session_switch()` events (`/resume`, `/new`, `/reset`, compression); a new `initialize()` call is the refresh boundary.

## Tool

The single schema is intentionally small:

```text
mind({
  "action": "store|search|correct|forget|confirm",
  ... action-specific fields ...
})
```

Search returns only bounded structured `{id, text}` hits. It does not include the upstream human-readable output a second time. Exact ids returned by search are accepted for `correct`; the adapter resolves them to the upstream command's text-hint interface.

## Activation

Select it in the active profile's configuration:

```yaml
memory:
  provider: hermes-mind
```

Start a new Hermes process after changing provider configuration. For a running gateway, restart it through your host's service manager, then start a fresh session. Check the selected provider with `hermes memory status`.

## Verification

Run from this repository with the active Hermes runtime Python so the real
`agent.memory_provider` API, token-estimate helper, and setup tests are imported.
Set `HERMES_PYTHON` to that interpreter's absolute path first:

```bash
"$HERMES_PYTHON" -m unittest discover -s tests -v
```

The tests use temporary profile roots and do not touch the active profile's memory, config, or gateway.

## Prompt-size measurement

The active Hermes runtime helper `agent.model_metadata.estimate_request_tokens_rough()` was used on the provider's actual wrapped tool schema (`{"type":"function", "function": ...}`) and startup block. It is Hermes' calibrated preflight estimate, not a universal provider tokenizer or an exact billable wire count; provider-specific framing and model tokenizers can differ. Startup facts are rendered as one standard JSON object inside a clearly labeled untrusted-data line, so quotes and newlines remain syntactically inside JSON strings. This is risk reduction and syntactic containment, not a guarantee that a model will ignore malicious memory text; the tests do not demonstrate model compliance. No semantic blacklist drops instruction-like facts.

Measured with Hermes Python 3.14.7 on October 20, 2026:

| Case | Startup chars | Startup tokens | Tool-schema tokens | Combined tokens |
|---|---:|---:|---:|---:|
| Representative English/Japanese facts | 392 | 119 | 146 | 265 |
| Worst-case Japanese input (20 long records) | 1203 | 1024 | 146 | 1170 |

The worst-case fixture is deliberately much larger than the retained snapshot. The adapter selects at most six records and fits the complete startup block, including headings, JSON quoting, and instructions, to 1024 Hermes-estimated tokens. Defensive character ceilings are 8192 for the block and 4000 per candidate. The combined startup-plus-tool bound is tested at 1400 estimated tokens. These are ceilings, not targets: small stores produce short blocks. These bounds cover the provider-owned additions only, not Hermes' rest of system prompt, conversation, or other tools.
