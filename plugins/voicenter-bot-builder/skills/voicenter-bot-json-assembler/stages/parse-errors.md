# Skill 3 stage — Parse error format and common deviations

*Load this only when the strict-template parse fails (Skill 3 §3). It carries the structured
error format the user sees and worked examples for the deviations that actually occur in
practice. The parse **rules** stay in SKILL.md — they gate everything; these are the error
outputs, needed only at the moment a parse fails.*

## Table of contents

- [Parse error format](#parse-error-format)
- [Common deviations and example messages](#common-deviations-and-example-messages)

---

## Parse error format

When a deviation is detected, halt and emit:

```
Skill 3 parse error.

Location: line <N> in <spec source>
Section: <section number, e.g., 4>
Expected: <pattern>
Found: <actual content, truncated to one line>

Fix: <one-line hint about the fix>

Skill 3 will not assemble. Re-run Skill 1 patch mode (if the spec was hand-edited or structurally invalid) or fix the deviation manually, then re-invoke Skill 3.
```

The `<spec source>` is the conversation message reference (single-conv) or the file path (Claude Code). Line numbers are within that source.

Skill 3 does not attempt to interpret around the deviation. It does not emit a partial JSON. It does not flag and continue. One deviation, one error, one halt.

## Common deviations and example messages

These are illustrative — the parser is grammar-driven, not pattern-matched, so anything off-grammar surfaces. The examples here are the most common shapes the user will see.

| Deviation | Example error |
|---|---|
| Missing section header | `Expected: '## 4. Intent List (Structural)'. Found: '## Intent List'. Fix: restore the section number and exact heading.` |
| Bold field label punctuation off | `Expected: '**Bot Name:** <value>'. Found: 'Bot Name: <value>'. Fix: wrap the label in bold markdown.` |
| Unknown marker shape wrong | `Expected: '<UNKNOWN: <description>>'. Found: '(UNKNOWN: ...)'. Fix: use angle brackets and the literal token UNKNOWN.` |
| Status marker synonym | `Expected: one of '[structural]', '[detailed]', '[detailed-revisit]'. Found: '[done]'. Fix: re-run Skill 2 to set the canonical marker.` |
| Intent identifier in section 5 has no match in section 4 | `Section 5 entry 'verify_caller_id' has no matching intent in section 4. Fix: re-run Skill 1 patch mode to add the intent or remove the orphan section 5 entry.` |
| Section 4 reference to undeclared transition target | `Intent 'validate_customer_address' transitions to 'get_slots', but no intent 'get_slots' exists in section 4 (closest match: 'get_available_slots'). Fix: re-run Skill 1 patch mode to correct the transition target.` |
| Spec ends mid-intent (truncated upload) | `Section 5 entry 'confirm_appointment' has no closing structure (no following section 6 header). Fix: re-attach the complete spec.` |
| RT-specific sub-label punctuation off | `Expected: '**URL:** <value>'. Found: 'URL: <value>'. Fix: wrap the sub-label in bold markdown.` |
| Bot-intent role value off-grammar | `Expected: '**Bot-intent role:** entry\|global\|chained'. Found: '**Bot-intent role:** start'. Fix: use one of the three canonical role values (or omit for chained).` |
| Terminal outcome missing slot assignment (v1.13.0) | `Expected: '**Terminal outcome:** <slot_name> = "<fixed value>"' or '**Terminal outcome:** <slot_name> = <capture/compose description>'. Found: '**Terminal outcome:** הלקוח אישר הכל'. Fix: name the owning slot and use '=' (quote the value only when it is a fixed pinned string).` |
| Sensitive value off-grammar (v1.13.0) | `Expected: '**Sensitive:** true\|false'. Found: '**Sensitive:** yes'. Fix: use lowercase true or false (or omit for false).` |
| IsSilenceIntent value off-grammar (v1.14.0) | `Expected: '**IsSilenceIntent:** true\|false'. Found: '**IsSilenceIntent:** 1'. Fix: use lowercase true or false (or omit for false).` |

The transition-target check (last two rows) blurs into cross-reference territory — it's caught at parse time because it's a dangling identifier discoverable from sections 4-5 alone, and Skill 3 already has the data. Treating it as a parse error rather than waiting for §15.4 lets the user fix one thing at a time.

---
