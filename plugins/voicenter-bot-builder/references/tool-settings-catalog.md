# Tool settings catalog

The settings each tool type takes: every setting's `ToolTypeConfigID` and its exact name, which
is the `ParameterName` a tool's static setting must carry. Read by Skill 1 when it captures a
tool's settings (spec section 4.8), and by CHK-34.

**The live read wins.** With a Voicenter MCP connected, Skill 1 reads `ToolTypeConfig` by
`ToolTypeId` (`GET /Tool/TypeConfig/{ToolTypeId}` → `Data.RequiredParameters[]`:
`ToolTypeConfigID` and name) and uses what it returns. This catalog is the fallback when no read
is reachable, and the list CHK-34 checks names against. When a live read disagrees with it, the
catalog is stale: record the live values in the spec, log the difference to spec section 7.3,
and update this file.

## Catalog (dated)

| Type | `ToolTypeId` | `ToolTypeConfigID` — setting name | Source |
|---|---|---|---|
| WebAPI | 10 | 18 `ApiEndpoint` · 21 `HttpMethod` · 24 `RequestPayload` · 27 `RequestHeaders` | live `ToolTypeConfig` read with `{ToolTypeId: 10}`, 2026-11-18 |
| MCP | 1 | 30 `ServerUrl` · 33 `AuthToken` · 36 `Timeout` | the import contract traced from API Manager's code, 2026-11-17 |
| Database | 13 | 39 `ConnectionString` · 42 `Query` · 45 `Timeout` | the import contract, 2026-11-17 |
| Email, SMS, FileStorage | 4, 7, 16 | — never in the file (added after the import) | — |

Names are exact and case-sensitive: `ApiEndpoint`, never `URL`; `HttpMethod`, never `Method`.

**Credentials.** `AuthToken` (33) and `ConnectionString` (39) always hold a credential, and so does
a `RequestHeaders` (27) value with an `Authorization`, API-key, token or cookie header. Their
value is never written: the spec records the credential marker and the person sets it on the
tool after the import.
