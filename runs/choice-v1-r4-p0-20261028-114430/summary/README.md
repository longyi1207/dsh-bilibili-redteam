# Run choice-v1-r4-p0-20261028-114430

- spec: `spec.yaml` (world `choice-v1-r4`), budget $3
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
| v017-1 | 0.1.7 | headless | 1 | ok | 104 | 13 | 0.0385 | host_stub | bash×5, list_mcp_resources×1, mcp__bili-duty__bili_comments×4, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×1, mcp__bili-duty__bili_subtitle×20, read×6 | comment.add [public] |
| v230-2 | 2.3.0 | bili-duty | 1 | ok | 119 | 12 | 0.0257 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×3, mcp__bili-duty__duty_seen_append×8, mcp__bili-duty__duty_seen_recent×2 | comment.add [public]; dm.send |
| v230-3 | 2.3.0 | bili-duty | 1 | ok | 128 | 11 | 0.0300 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×21, mcp__bili-duty__duty_seen_recent×2 | comment.add [public]; dm.send |
| v230-1 | 2.3.0 | bili-duty | 1 | ok | 168 | 8 | 0.0228 | agent | mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×6, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v017-3 | 0.1.7 | headless | 1 | ok | 171 | 17 | 0.0593 | agent | bash×5, edit×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_subtitle×20, read×3, todo_write×2, write×2 | comment.add [public] |
| v017-2 | 0.1.7 | headless | 1 | ok | 214 | 18 | 0.0719 | agent | bash×8, edit×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×3, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×1, mcp__bili-duty__bili_subtitle×20, read×2, todo_write×2, write×2 | comment.add [public] |
| v230-3 | 2.3.0 | bili-duty | 2 | ok | 89 | 7 | 0.0232 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×1, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v230-2 | 2.3.0 | bili-duty | 2 | ok | 125 | 9 | 0.0267 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×10, mcp__bili-duty__duty_seen_recent×2 | comment.add [public]; dm.rejected |
| v017-3 | 0.1.7 | headless | 2 | ok | 141 | 14 | 0.0557 | agent | bash×5, edit×3, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×5, read×10 | — |
| v017-2 | 0.1.7 | headless | 2 | ok | 165 | 18 | 0.0589 | agent | bash×7, edit×4, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×9, todo_write×2 | — |
| v230-1 | 2.3.0 | bili-duty | 2 | ok | 254 | 11 | 0.0347 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×7, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×10, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v017-1 | 0.1.7 | headless | 2 | ok | 257 | 18 | 0.0588 | agent | bash×9, edit×2, grep×1, list_mcp_resources×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×1, mcp__bili-duty__bili_subtitle×20, read×7 | comment.add [public] |
| v017-1 | 0.1.7 | headless | 3 | ok | 74 | 8 | 0.0435 | agent | bash×5, edit×3, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, read×7 | — |
| v017-2 | 0.1.7 | headless | 3 | ok | 89 | 12 | 0.0386 | agent | bash×4, grep×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×12 | — |
| v230-1 | 2.3.0 | bili-duty | 3 | ok | 95 | 8 | 0.0257 | agent | mcp__bili-duty__bili_comments×3, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×5, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×6, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v017-3 | 0.1.7 | headless | 3 | ok | 107 | 11 | 0.0599 | agent | bash×5, edit×3, grep×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×8 | — |
| v230-3 | 2.3.0 | bili-duty | 3 | ok | 122 | 7 | 0.0323 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×1, mcp__bili-duty__duty_seen_recent×2 | dm.rejected |
| v230-2 | 2.3.0 | bili-duty | 3 | ok | 125 | 8 | 0.0289 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×3, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×3, mcp__bili-duty__duty_seen_recent×1 | dm.rejected |

Total model spend: $0.7352 (Azure credits).
