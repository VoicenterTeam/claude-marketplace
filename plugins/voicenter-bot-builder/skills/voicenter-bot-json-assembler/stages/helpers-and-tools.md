# Skill 3 stage — Helpers and tools (spec section 4.8)

*Load at §3 and §4 when the spec has `## 4.8 Helpers and Tools`; without it nothing here
applies and `intentList` carries no `subAgents` or `subAgentTools` key. The import's rules for
these lists are in `${CLAUDE_PLUGIN_ROOT}/references/voicebot-json-contract.md` §8; CHK-29…CHK-39
verify them.*

## Table of contents

- [1. Parse rules](#1-parse-rules)
- [2. Assembly](#2-assembly)
- [3. Banner](#3-banner)

---

## 1. Parse rules

Section 4.8 sits after 4.6 (and 4.7 when present), before `## 5. Intent Details`. It holds
`### Helper: <identifier>` blocks, then `### Tool: <ToolName>` blocks. Labels are exact.

**Helper block** (`<identifier>` snake_case, unique among helpers):

| Label | Value |
|---|---|
| `**Name:**` | required free text — `SubAgentName` |
| `**Title:**` | free text — `SubAgentTitle` |
| `**Description:**` | free text — `SubAgentDescription` |
| `**Serves intents:**` | comma-separated section-4 intent identifiers, at least one |
| `**AI model:**` | an integer AI model ID, optionally followed by ` — <note>`, or `<UNKNOWN: …>` |
| `**Knowledge bases to link after the import:**` | `[none]`, or `<KnowledgeBaseID or <UNKNOWN: …>> — <name>` items separated by `; ` |

**Tool block** (`<ToolName>` as the file will name it):

| Label | Value |
|---|---|
| `**Display name:**` | free text — `ToolDisplayName` (defaults to the ToolName) |
| `**Purpose:**` | free text for human review — not emitted |
| `**Type:**` | an integer type, optionally ` — <name>`: `1` MCP, `10` WebAPI, `13` Database; `4` Email, `7` SMS, `16` FileStorage |
| `**Risk:**` | `1` Read, `2` Action, `3` Destructive or `4` External, optionally ` — <name>` |
| `**Settings:**` | numbered lines `<ParameterName> — config <ToolTypeConfigID or <UNKNOWN: …>> — <`value` in backticks, or <UNKNOWN: …>>`, or `[none…]` |
| `**Arguments:**` | numbered lines `<name> — string\|integer\|number\|boolean, required\|optional`, or `[none]` |
| `**Used by:**` | comma-separated helper identifiers from this section |
| `**Add after the import:**` | the reason the tool is created after the import; **required** on types 4, 7 and 16 |

**Section 5 entries**, after the intents, one per helper and per tool, each with `**Status:**`:
`### Helper: <identifier>` carries a fenced `**Instruction:**`; `### Tool: <ToolName>` carries a
fenced `**Tool description:**` and, when it has arguments, `**Arguments:**` lines
``- `<name>` — Description: <text>``. Gate A counts them like intents.

**Parse errors** (format as `parse-errors.md`): a served intent that is not a section-4
intent; a `**Used by:**` name that is not a helper here; a helper or tool without its section-5
entry, or an entry without its block; a type 4, 7 or 16 tool without `**Add after the import:**`;
an `**AI model:**`, `**Type:**`, config or knowledge-base ID that is neither an integer nor
`<UNKNOWN: …>`; a `**Risk:**` outside 1–4; a helper without `**Name:**`.

## 2. Assembly

### 2.1 Labels

| ID kind | Range | Rule |
|---|---|---|
| `SubAgentID` | `-5000, -5001, …` | one per helper, in section-4.8 order |
| `ToolId` | `-6000, -6001, …` | one per **emitted** tool (not `**Add after the import:**`), in section-4.8 order |

`IntentIds` are the helper's served intents' `IntentId` labels (§4.1), in the order written.
`ToolAssignments[].ToolId` is the label of each emitted tool whose `**Used by:**` names the
helper, in section-4.8 tool order.

### 2.2 `intentList.subAgents[]` and `subAgentTools[]`

Emit both keys after `apiSilenceRelations`, `subAgents` first. Field order per helper:

| Key | Source |
|---|---|
| `SubAgentID` | §2.1 |
| `SubAgentName`, `SubAgentTitle`, `SubAgentDescription` | `**Name:**`, `**Title:**` (`""` when absent), `**Description:**` (`""` when absent) |
| `SubAgentStatusID` | `1` |
| `Instruction` | section 5 `**Instruction:**`, verbatim |
| `AiModelId` | `**AI model:**`; `-999` for `<UNKNOWN: …>` |
| `IntentIds` | §2.1 |
| `KnowledgeBases` | `[{"KnowledgeBaseID", "KnowledgeBaseName"}]` per listed knowledge base (`-999` for an unknown ID); `[]` for `[none]`. The import links none; it reports each one, which is how §7.6 finds the new helper's ID |
| `ToolAssignments` | `[{"ToolId", "IsEnabled": 1, "Parameters": [], "ConditionList": []}]` per §2.1 |

Per emitted tool:

| Key | Source |
|---|---|
| `ToolId` | §2.1 |
| `ToolName`, `ToolDisplayName` | the block's name; `**Display name:**` |
| `ToolTypeId` | `**Type:**` |
| `ToolExecutionTypeID` | `2` (AI) |
| `Description` | section 5 `**Tool description:**`, verbatim |
| `IsActive`, `ToolStatusID` | `1`, `1` |
| `ToolRiskTypeID` | `**Risk:**` |
| `ParameterSchemaJson` | only when the tool has arguments: `{"type": "object", "required": [<required names>], "properties": {<name>: {"type", "description"}}, "additionalProperties": false}`, descriptions from section 5 |
| `Parameters` | each setting `{"ToolTypeConfigID", "ParameterName", "ToolParameterSourceID": 5, "Config": {"value": "<string>"}}`, then each argument `{"ToolTypeConfigID": null, "ParameterName", "ToolParameterSourceID": 1, "Config": {"source_filed": "<name>"}}` — the key is spelled `source_filed`, as the import reads it |
| `ToolVersion` | `{"VersionNumber": "1.0.0", "Description": "First version", "ConfigurationJson": {}}` |

Never emit `TemplateId`, and never `null` except an argument's `ToolTypeConfigID`. A config ID
`<UNKNOWN: …>` emits `-999`; a setting value `<UNKNOWN: X>` emits `"<USER_TO_FILL: X>"`. A value
whose marker starts `credential` is a credential: it stays that marker, never a value.

## 3. Banner

When section 4.8 exists, the banner adds, after DEFAULTS APPLIED:

```
# HELPERS AND TOOLS:
#   - Helper <SubAgentID> "<Name>" — serves <intent identifiers>; AI model <AiModelId>; tools <ToolNames | none>
#   - Tool <ToolId> "<ToolName>" — type <n> <type name>; risk <n>; used by <helper names>
#   - A tool name already taken on the account is created as <name>_<new ToolId>, without a word; the
#     helper's instruction then names the old name — check each tool's name after the import.
#
# MANDATORY POST-IMPORT STEP (helpers and tools — one line per item):
#   - Link knowledge base <id> "<name>" to helper "<Name>" — the import never links one.
#   - Create tool "<ToolName>" (type <n> <type name>) with its own credential and assign it to
#     <helper names>: <the block's Add-after-the-import reason>
#   - Set <setting> on tool "<ToolName>" by hand — a credential, never written into the file.
```

UNKNOWN VALUES lists a credential marker with the note `credential — not a value to type here:
delete this Parameters item before a manual import; set it on the tool after the import`.
Omit the MANDATORY section when it has no line.
