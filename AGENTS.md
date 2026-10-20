# Development guide

Before changing this plugin, read [.agents/skills/hermes-mind-provider-development/SKILL.md](.agents/skills/hermes-mind-provider-development/SKILL.md) for the development and verification workflow. Keep plugin-specific lessons there rather than in a globally installed skill.

## Constraints

- Keep this a thin adapter through Hermes' public memory-provider API. Built-in memory and LCM remain separate.
- Keep recalled facts untrusted, bounded, and separate from the static system policy. Do not add automatic extraction, extra LLM calls, or background timers.
- Keep state profile-local; only the primary agent context may initialize or mutate it. Never test against the active memory store.
- Fetch the pinned upstream artifact only through explicit setup, with hash verification; never download at runtime or modify upstream algorithms.
- Do not restart the gateway from an agent. Ask the operator when a restart is required.

## Verification

Use the active Hermes runtime Python, not an arbitrary system Python. From this repository, with `HERMES_PYTHON` set to that interpreter:

```sh
"$HERMES_PYTHON" -m unittest discover -s tests -v
```

See [README.md](README.md) for setup, activation, refresh semantics, and snapshot limits. Preserve unrelated working-tree changes; do not activate the provider or change live configuration merely to run tests.
