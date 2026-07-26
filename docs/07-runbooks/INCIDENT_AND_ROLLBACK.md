# Incident and Rollback Runbook

## Trigger conditions

Use this runbook when:

- deployment fails;
- critical regression appears;
- data integrity is at risk;
- security controls fail;
- service health degrades beyond agreed thresholds.

## Immediate actions

1. stop further deployments;
2. identify affected version and environment;
3. preserve logs and evidence;
4. assess user and data impact;
5. decide rollback, roll-forward, or containment;
6. communicate status;
7. record all actions.

## Rollback checklist

- [ ] rollback version identified;
- [ ] database compatibility verified;
- [ ] backup or restore point confirmed;
- [ ] operator assigned;
- [ ] rollback executed;
- [ ] health checks pass;
- [ ] critical workflows verified;
- [ ] incident log updated.
