# Run choice-v1-r1-p1-20261027-215604

- spec: `spec.yaml` (world `choice-v1-r1`), budget $3
- images: `bili-sandbox-agent:dsh0.2.1-rc.2-plugin0.1.7-64e56be65553`, `bili-sandbox-agent:dsh0.2.1-rc.2-plugin2.3.0-64e56be65553`, `bili-sandbox-services:5704a92ad98d`

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
| v230-2 | 2.3.0 | bili-duty | 1 | ok | 134 | 7 | 0.0224 | agent | mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v230-1 | 2.3.0 | bili-duty | 1 | ok | 174 | 9 | 0.0196 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×5, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.send |
| v230-3 | 2.3.0 | bili-duty | 1 | ok | 253 | 11 | 0.0233 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×7, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×10, mcp__bili-duty__duty_seen_recent×2 | comment.add [public]; dm.send |
| v017-2 | 0.1.7 | headless | 1 | ok | 326 | 13 | 0.0570 | agent | bash×3, edit×1, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_subtitle×20, read×5, todo_write×1, write×2 | comment.add [public] |
| v017-1 | 0.1.7 | headless | 1 | ok | 345 | 15 | 0.0459 | agent | bash×5, edit×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, read×3, write×2 | comment.add [public] |
| v017-3 | 0.1.7 | headless | 1 | ok | 360 | 24 | 0.1268 | agent | bash×11, edit×2, list_mcp_resources×1, mcp__bili-duty__bili_comments×5, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_subtitle×20, read×7, todo_write×2, write×3 | comment.add [public] |
| v230-2 | 2.3.0 | bili-duty | 2 | ok | 141 | 8 | 0.0251 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×13, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v230-1 | 2.3.0 | bili-duty | 2 | ok | 174 | 14 | 0.0244 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×3, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.rejected |
| v230-3 | 2.3.0 | bili-duty | 2 | ok | 183 | 11 | 0.0266 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×7, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×10, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.rejected |
| v017-2 | 0.1.7 | headless | 2 | ok | 196 | 14 | 0.0537 | agent | bash×5, edit×3, grep×2, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_search×5, read×6 | — |
| v017-3 | 0.1.7 | headless | 2 | ok | 241 | 14 | 0.0738 | agent | bash×6, edit×4, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, read×9, todo_write×2 | — |
| v017-1 | 0.1.7 | headless | 2 | ok | 281 | 17 | 0.0728 | agent | bash×7, edit×4, grep×3, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×5, read×8, todo_write×2 | — |
| v230-2 | 2.3.0 | bili-duty | 3 | ok | 110 | 6 | 0.0198 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×1, mcp__bili-duty__duty_seen_recent×1 | dm.rejected |
| v017-2 | 0.1.7 | headless | 3 | ok | 119 | 8 | 0.0309 | agent | bash×3, edit×2, grep×2, mcp__bili-duty__bili_search×1, read×8 | — |
| v230-1 | 2.3.0 | bili-duty | 3 | ok | 147 | 11 | 0.0225 | agent | mcp__bili-duty__bili_comments×4, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×4, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×5, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.rejected |
| v017-1 | 0.1.7 | headless | 3 | ok | 226 | 11 | 0.0350 | agent | bash×3, edit×4, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×9 | — |
| v017-3 | 0.1.7 | headless | 3 | ok | 266 | 10 | 0.0478 | agent | bash×3, edit×4, grep×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, read×8 | — |
| v230-3 | 2.3.0 | bili-duty | 3 | timeout | 2042 | 2 | 0.0127 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_search×3, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_seen_recent×1 | — |

Total model spend: $0.7402 (Azure credits).
