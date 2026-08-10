---
description: Fill in an Agent Spec's per-intent language content (Skill 2)
---

Invoke the `voicenter-bot-builder:voicenter-bot-intent-detail-author` skill and follow it from
the top.

Hand over immediately. The skill builds its own work queue by scanning the spec's section-5
status markers — every intent marked `[structural]` or `[detailed-revisit]` — and proposes its
own batching plan. Do not pre-select intents, do not assume where a previous run stopped, and
do not skip the batch checkpoints: the spec is the state, and it is re-read on every
invocation.

$ARGUMENTS
