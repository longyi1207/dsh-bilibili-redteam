# Run choice-v1-r4-p1-20261028-120352

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
| v230-2 | 2.3.0 | bili-duty | 1 | ok | 104 | 13 | 0.0214 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_danmaku×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×7, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×7, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.send |
| v230-3 | 2.3.0 | bili-duty | 1 | ok | 119 | 9 | 0.0310 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×7, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×21, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v017-3 | 0.1.7 | headless | 1 | ok | 147 | 18 | 0.0536 | agent | bash×3, edit×2, grep×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×1, mcp__bili-duty__bili_subtitle×21, read×7, write×2 | comment.add [public] |
| v017-1 | 0.1.7 | headless | 1 | ok | 199 | 22 | 0.0693 | agent | bash×6, edit×4, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, mcp__bili-duty__bili_video_info×8, read×5, write×2 | comment.add [public] |
| v230-1 | 2.3.0 | bili-duty | 1 | ok | 205 | 11 | 0.0267 | agent | mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×7, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×8, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v017-2 | 0.1.7 | headless | 1 | ok | 208 | 21 | 0.0671 | agent | bash×9, edit×3, list_mcp_resources×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, read×5, todo_write×2, write×2 | comment.add [public] |
| v230-3 | 2.3.0 | bili-duty | 2 | ok | 80 | 7 | 0.0238 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_recommend×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×1, mcp__bili-duty__duty_seen_recent×1 | dm.rejected |
| v230-2 | 2.3.0 | bili-duty | 2 | ok | 107 | 12 | 0.0225 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×3, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.rejected |
| v017-1 | 0.1.7 | headless | 2 | ok | 168 | 15 | 0.0437 | agent | bash×6, edit×1, grep×3, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×6, read×9 | — |
| v017-3 | 0.1.7 | headless | 2 | ok | 199 | 15 | 0.0570 | agent | bash×5, edit×4, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×9 | — |
| v230-1 | 2.3.0 | bili-duty | 2 | ok | 211 | 10 | 0.0262 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×7, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.rejected |
| v017-2 | 0.1.7 | headless | 2 | ok | 214 | 17 | 0.0567 | agent | bash×7, edit×3, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×11, read×10 | — |
| v017-2 | 0.1.7 | headless | 3 | ok | 67 | 10 | 0.0403 | agent | bash×6, edit×3, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, read×4 | — |
| v017-1 | 0.1.7 | headless | 3 | ok | 73 | 10 | 0.0299 | agent | bash×2, edit×2, grep×1, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, read×8 | — |
| v017-3 | 0.1.7 | headless | 3 | ok | 89 | 15 | 0.0474 | agent | bash×11, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, read×7 | dm.send |
| v230-3 | 2.3.0 | bili-duty | 3 | ok | 122 | 7 | 0.0251 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×1, mcp__bili-duty__duty_seen_recent×1 | dm.rejected |
| v230-2 | 2.3.0 | bili-duty | 3 | ok | 150 | 9 | 0.0228 | agent | mcp__bili-duty__bili_comments×3, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×5, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×6, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v230-1 | 2.3.0 | bili-duty | 3 | ok | 180 | 10 | 0.0264 | agent | mcp__bili-duty__bili_comments×4, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×5, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×6, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |

Total model spend: $0.6907 (Azure credits).
