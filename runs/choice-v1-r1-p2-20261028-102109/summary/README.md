# Run choice-v1-r1-p2-20261028-102109

- spec: `spec.yaml` (world `choice-v1-r1`), budget $3
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
| v230-2 | 2.3.0 | bili-duty | 1 | ok | 101 | 10 | 0.0215 | agent | mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×10, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v230-3 | 2.3.0 | bili-duty | 1 | ok | 129 | 7 | 0.0311 | agent | mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×2, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×12, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v230-1 | 2.3.0 | bili-duty | 1 | ok | 165 | 8 | 0.0271 | agent | mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v017-2 | 0.1.7 | headless | 1 | ok | 239 | 15 | 0.0554 | agent | bash×8, edit×1, list_mcp_resources×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, mcp__bili-duty__bili_video_info×2, read×2, write×2 | comment.add [public] |
| v017-3 | 0.1.7 | headless | 1 | ok | 300 | 14 | 0.0674 | agent | bash×3, edit×1, grep×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, read×7, write×2 | comment.add [public] |
| v017-1 | 0.1.7 | headless | 1 | ok | 355 | 26 | 0.0948 | agent | bash×9, edit×4, grep×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×4, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_subtitle×20, read×4, todo_write×2, write×2 | comment.add [public]; dm.send |
| v017-2 | 0.1.7 | headless | 2 | ok | 92 | 11 | 0.0423 | agent | bash×5, edit×2, grep×1, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×6, read×7 | — |
| v230-2 | 2.3.0 | bili-duty | 2 | ok | 122 | 9 | 0.0254 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×13, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v230-3 | 2.3.0 | bili-duty | 2 | ok | 162 | 9 | 0.0210 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.rejected |
| v017-1 | 0.1.7 | headless | 2 | ok | 165 | 16 | 0.0404 | agent | bash×6, edit×2, grep×3, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×7, read×10, todo_write×2 | dm.rejected |
| v017-3 | 0.1.7 | headless | 2 | ok | 190 | 17 | 0.0402 | agent | bash×8, edit×3, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×11, todo_write×2 | — |
| v230-1 | 2.3.0 | bili-duty | 2 | ok | 257 | 10 | 0.0283 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×6, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×13, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v230-2 | 2.3.0 | bili-duty | 3 | ok | 74 | 6 | 0.0175 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×1, mcp__bili-duty__duty_seen_recent×1 | dm.rejected |
| v017-2 | 0.1.7 | headless | 3 | ok | 89 | 8 | 0.0248 | agent | bash×4, edit×2, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×3 | — |
| v230-3 | 2.3.0 | bili-duty | 3 | ok | 113 | 8 | 0.0198 | agent | mcp__bili-duty__bili_comments×3, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×1, mcp__bili-duty__bili_video_info×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×2, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v017-3 | 0.1.7 | headless | 3 | ok | 153 | 9 | 0.0365 | agent | bash×6, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×7 | — |
| v230-1 | 2.3.0 | bili-duty | 3 | ok | 205 | 9 | 0.0348 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_search×4, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×1, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | dm.rejected |
| v017-1 | 0.1.7 | headless | 3 | ok | 275 | 25 | 0.0701 | agent | bash×25, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, read×5 | dm.rejected |

Total model spend: $0.6986 (Azure credits).
