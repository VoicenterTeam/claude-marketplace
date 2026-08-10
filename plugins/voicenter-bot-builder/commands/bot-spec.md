---
description: Design or patch a Voicenter bot's Agent Spec (Skill 1)
---

Invoke the `voicenter-bot-builder:voicenter-bot-spec-designer` skill and follow it from the
top.

Hand over immediately — do not pre-interpret the user's request, and do not decide anything
this command could get wrong. The skill detects its own runtime and its own mode: a spec
attached or present in the workspace means patch mode, no spec means greenfield. Whatever the
user typed after the command is context for the skill's interview, not an instruction to act
on first.

$ARGUMENTS
