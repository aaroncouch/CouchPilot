# Checkpoint

Run only when the operator invokes `/couch-checkpoint`. Requires an active
session under `.session/`. Do not dispatch subagents; perform filesystem edits
in place following the core contract.

{{core}}
