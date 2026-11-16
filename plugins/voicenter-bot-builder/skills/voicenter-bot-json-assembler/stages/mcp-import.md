# Skill 3 stage — Import through a Voicenter MCP

*Load at §7.6, after the file is emitted and verified, and only when the person wants it
imported now. The endpoint's behaviour is in
`${CLAUDE_PLUGIN_ROOT}/references/voicebot-json-contract.md` §7 (helpers and tools: §8).*

## Table of contents

- [1. Before anything is sent](#1-before-anything-is-sent)
- [2. Import as a previewed plan](#2-import-as-a-previewed-plan)
- [3. When the step fails](#3-when-the-step-fails)
- [4. A tool without a preview](#4-a-tool-without-a-preview)
- [5. After the import: helpers and tools](#5-after-the-import-helpers-and-tools)

## 1. Before anything is sent

1. **Read what the connected Voicenter MCP lists** (the `voicenter-mcp` plugin or any other
   Voicenter connection). Pick the path:
   - `PlanPreview` and `PlanRun` are listed, and `VoiceBotImport` is listed or found through
     `SearchOperations` (read its card with `DescribeOperation`): §2.
   - Only `import_agent`, or `VoiceBotImport` without `PlanPreview`: §4.
   - Neither: give the §7.4 manual hand-off and stop.
2. **Replace every marker.** For each `<USER_TO_FILL: …>` string and `-999` ID in the banner's
   UNKNOWN VALUES, ask the person for the value — for `AccountID`, offer the MCP's account list;
   it must be one of the caller's accounts, or the import answers `403` — and write it into the
   emitted file at every place the sentinel went (for `AccountID`, also each
   `intents[].AccountId` and `intentCategories[].AccountId`). For a helper's `AiModelId`,
   offer `VoiceBotConfData`'s `Data.AiModelList` (active ones — an AI model, not a model
   configuration); for a `ToolTypeConfigID`, `ToolTypeConfig` for the tool's type; for a
   `KnowledgeBaseID`, `KnowledgeBaseList` (each read directly or through `SearchOperations` /
   `ExecuteRead`). **Never import a file that still carries a marker.** The spec keeps its
   `<UNKNOWN: …>`; tell the person that Skill 1 patch mode records the value so the next assembly
   carries it. **Credential markers** (`<USER_TO_FILL: credential …>`) are the exception: never ask
   for the value; leave that `Parameters` item out of the arguments and keep it for §5.
3. **Build the arguments** from the file: exactly `Name`, `AccountID`, `Description`,
   `BotStatusId`, `BotLanguages`, `AiModelConfig`, `ActiveVersionInfo`, `intentList`. Leave out
   `BotID`, `CreatedDate` and `ModifiedDate`: the import ignores them and the MCP refuses any key
   it does not declare. The file itself keeps them, for the manual and older import paths.

## 2. Import as a previewed plan

1. Call `PlanPreview` with one step:
   ```json
   {"step": 1, "tool": "VoiceBotImport", "args": <the arguments of §1.3>, "expect": "<one plain sentence>"}
   ```
   `expect` says, in the person's language, what they get — e.g. *"Creates the bot 'Brightview
   Family Clinic Assistant' on account 4471, switched off."*
2. Show the preview as the server returns it, then ask via `AskUserQuestion`: "Import now" /
   "Don't import".
3. Only on "Import now", call `PlanRun` with the preview's hash. Otherwise stop: nothing was imported.
4. Report from the run's answer: the new bot's ID, what the server's read-back confirmed, and each
   entry of `Data.Removed` — transfer targets the import dropped (all but the global hang-up),
   which the person sets again in the UI, and, for a file with helpers, the entries §5 acts on.
   The banner's MANDATORY POST-IMPORT steps still apply; with helpers, continue with §5.
5. Append to spec section 7.3, in either outcome:
   `[ISO-8601 timestamp]  Skill 3  importing  Bot <ID> on account <AccountID>.` or
   `… Refused: <ReasonPhrase>.` / `… Not run.` / `… Outcome unknown.`

## 3. When the step fails

A refusal comes back as a failed step with its reason and data. Act on the ReasonPhrase:

| ReasonPhrase | Do |
|---|---|
| `ai_model_config_unusable` | Offer `Data.GlobalAiModelConfigs` (`AIModelConfigID` — `Name`) via `AskUserQuestion`. If the pick is in `${CLAUDE_PLUGIN_ROOT}/skills/voicenter-bot-spec-designer/model-catalog.md` with the same wire family as the spec's model, put its `AIModelConfigID`, `AIModelTypeId` (as `AIModel`) and name in `AiModelConfig` (keeping `AccountId: 0`) and `ActiveVersionInfo.AIModelConfigId`, then preview again (§2). Otherwise the wire shape changes with the model: route the person to Skill 1 patch mode to change `**AI Model Config:**`, then Skill 3 again. Either way, tell them to record the model in the spec. |
| `import_placeholder_clash` | Nothing was stored. `Data` names `List`, `Field`, `Id`, `Index` and `Problem`. For `IntentRelatedID`, `BotIntentId` or `ParameterId`, give the named item an unused ID from its §4.1 range (and the `IntentConditionRelationID` that mirrors it), re-run `${CLAUDE_PLUGIN_ROOT}/references/verification-procedure.md` against the fixed file, then preview again. For `IntentId` or `IntentCategoryId`, other items point at the ID: tell the person to run Skill 3 on the spec again instead. Either way the file changed after CHK-27 or CHK-27 missed it — say so. |
| any other | Show the reason and its data; change nothing; stop. |

**Not known whether it took effect** — a 5xx, a timeout, a lost connection: read the account
first with `VoiceBotList` (directly or through the router; where it isn't offered, ask the person
to check the account in the UI). If a bot with this `Name` is there, show it and let the person
decide; never send the import again before that read.

## 4. A tool without a preview

`import_agent` (and `VoiceBotImport` on a server without plans) creates the bot at once, with no
preview. Say so, and ask via `AskUserQuestion`: "Import now" / "Import by hand". Only on "Import
now", call it with the §1.3 arguments, restricted to the keys its schema declares, and report the
bot ID it returns. §3's unknown-outcome rule, §2's log line and §5 apply.

## 5. After the import: helpers and tools

Only when the file has `intentList.subAgents`. Read every `Data.Removed` entry by `Type`
(`${CLAUDE_PLUGIN_ROOT}/references/voicebot-json-contract.md` §8):

| `Type` | Do |
|---|---|
| `KnowledgeBase` | Offer to link it (step 1). `SourceId` is the knowledge base, `NewEntityId` the new helper. |
| `ToolSecret` | Tell the person to set the setting the `Reason` names on the tool `Name` by hand. |
| `Tool`, `ToolAssignment`, `ToolTemplate`, any other | List it for the person to set by hand: what, on which helper or tool, and the `Reason` as given. |

1. **Link the knowledge bases.** For the `KnowledgeBase` entries, read
   `KnowledgeBaseAssignmentCreate`'s card with `DescribeOperation`, then `PlanPreview` one step per
   entry: `KnowledgeBaseAssignmentTypeID` `4`, the knowledge base `SourceId`, the entity
   `NewEntityId`, under the input names the card gives. Show the preview, ask via `AskUserQuestion`
   ("Link now" / "I'll link them myself"), and `PlanRun` only on "Link now".
2. **Add the tools the spec marks `**Add after the import:**`.** Offer each via `AskUserQuestion`
   ("Add it now" / "Later, by hand"). On "Add it now", in one previewed plan with the inputs each
   card requires: the tool's own credential (`CredentialCenterList` for one the person names, or
   `CredentialCenterAssignmentCreate`), `ToolCreate` in the account, then `ToolAssignmentCreate`
   with `EntityType` `7` on each helper that uses it. Ask for any input the spec does not give;
   never guess one. A helper's new ID comes from a `Data.Removed` entry naming it (`NewEntityId`);
   when none does, find a sub-agent read through `SearchOperations` and match by `SubAgentName`,
   or leave the step to the person in the UI. Then tell the person the helper's instruction does
   not name the new tool yet (Skill 2 on the spec, then update the helper).
3. **Credential settings left out** (§1.2): list each — setting and tool — to set on the tool by
   hand.
4. **Tool names.** A taken name is created as `<name>_<new ToolId>` without a word. When a read of
   the account's tools is offered, compare each `ToolName`; for a renamed one, tell the person the
   helper's instruction still names the old name.
5. Append to spec section 7.3: `[ISO-8601 timestamp]  Skill 3  importing  Helpers: <n> knowledge
   bases linked, <n> tools added, <n> items left to set by hand.`
