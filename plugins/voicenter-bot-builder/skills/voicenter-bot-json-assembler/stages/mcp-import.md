# Skill 3 stage — Import through a Voicenter MCP

*Load at §7.6, after the file is emitted and verified, and only when the person wants it
imported now. The endpoint's behaviour is in
`${CLAUDE_PLUGIN_ROOT}/references/voicebot-json-contract.md` §7.*

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
   `intents[].AccountId` and `intentCategories[].AccountId`). **Never import a file that still
   carries a marker.** The spec keeps its `<UNKNOWN: …>`; tell the person that Skill 1 patch mode
   records the value so the next assembly carries it.
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
   which the person sets again in the UI. The banner's MANDATORY POST-IMPORT steps still apply.
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
bot ID it returns. §3's unknown-outcome rule and §2's log line apply.
