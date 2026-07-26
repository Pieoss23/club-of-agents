# Risk Matrix

| Level | Examples | Minimum review |
|---|---|---|
| Low | isolated docs, small internal refactor | one reviewer |
| Medium | feature behavior, public API extension, dependency update | independent reviewer + CI |
| High | authentication, authorization, migrations, shared schemas, destructive operations | specialist review + rollback evidence |
| Critical | production data transformation, security boundary, irreversible operation | Project Master + specialist reviewers + staged rollout |

Risk can be raised by any agent. Only the Project Master or designated authority may lower it.
