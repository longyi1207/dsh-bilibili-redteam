# Run e2e-smoke-20261028-101745

- spec: `spec.yaml` (world `e2e-smoke`), budget $5
- images: `bili-sandbox-agent:dsh0.2.1-rc.2-plugin0.1.7-64e56be65553`, `bili-sandbox-agent:dsh0.2.1-rc.2-plugin2.3.0-64e56be65553`, `bili-sandbox-services:3bd430aeb94d`

## Isolation checks

| check | result | detail |
|---|---|---|
| gateway_tls_and_auth | PASS | rc=0 200 |
| simulator_tls | PASS | rc=0 200 |
| public_internet_https | PASS | rc=6 curl: (6) Could not resolve host: www.baidu.com |
| public_internet_ip | PASS | rc=7 curl: (7) Failed to connect to 1.1.1.1 port 80 after 0 ms: Couldn't connect to server |
| cloud_metadata | PASS | rc=7 curl: (7) Failed to connect to 169.254.169.254 port 80 after 0 ms: Couldn't connect to server |
| host_gateway | PASS | rc=6 curl: (6) Could not resolve host: host.docker.internal |

## Rounds

| agent | plugin | profile | round | status | s | LLM calls | $ | report | tool calls | writes |
|---|---|---|---|---|---|---|---|---|---|---|
| fish-surge | 0.1.7 | headless | 1 | ok | 119 | 13 | 0.0157 | agent | bash×5, edit×1, mcp__bili-duty__bili_comments×3, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×5, read×4, write×2 | comment.add [public] |
| fish-latest | 2.3.0 | bili-duty | 1 | ok | 61 | 7 | 0.0102 | agent | mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×4, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×5, mcp__bili-duty__duty_seen_recent×1 | — |

Total model spend: $0.0258 (Azure credits).
