---
description: Assemble a fully-detailed Agent Spec into deployable bot JSON (Skill 3)
---

Invoke the `voicenter-bot-builder:voicenter-bot-json-assembler` skill and follow it from the
top.

Hand over immediately. The skill runs its own pre-flight gates, parses the spec strictly,
assembles in memory, and runs the 26-check verification pass before anything is emitted. Do not
attempt to assemble or shortcut any part of that yourself, and do not ask the skill to skip
verification — a spec that fails a blocking check produces no JSON by design, and the failure
report names which skill to go back to.

$ARGUMENTS
