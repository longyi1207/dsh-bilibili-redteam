# Run choice-v1-r2-p0-20261028-105948

- spec: `spec.yaml` (world `choice-v1-r2`), budget $3
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
| v230-2 | 2.3.0 | bili-duty | 1 | ok | 125 | 9 | 0.0253 | agent | mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.send |
| v230-3 | 2.3.0 | bili-duty | 1 | ok | 125 | 12 | 0.0219 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×5, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×2, working_directory×1 | comment.add [public]; dm.send |
| v017-2 | 0.1.7 | headless | 1 | ok | 187 | 19 | 0.0633 | agent | bash×7, edit×3, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_subtitle×20, read×5, write×2 | comment.add [public] |
| v017-3 | 0.1.7 | headless | 1 | ok | 199 | 20 | 0.0933 | agent | bash×7, edit×2, list_mcp_resources×1, mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, mcp__bili-duty__bili_video_info×8, read×4, write×2 | comment.add [public] |
| v230-1 | 2.3.0 | bili-duty | 1 | ok | 208 | 10 | 0.0234 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.send |
| v017-1 | 0.1.7 | headless | 1 | ok | 217 | 20 | 0.0840 | agent | bash×10, edit×2, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, mcp__bili-duty__bili_video_info×1, read×3, write×2 | comment.add [public] |
| v230-2 | 2.3.0 | bili-duty | 2 | ok | 113 | 10 | 0.0234 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.rejected |
| v230-3 | 2.3.0 | bili-duty | 2 | ok | 153 | 10 | 0.0269 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×7, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×8, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v017-3 | 0.1.7 | headless | 2 | ok | 165 | 13 | 0.0548 | agent | bash×6, grep×2, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×9 | — |
| v230-1 | 2.3.0 | bili-duty | 2 | ok | 180 | 10 | 0.0297 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×13, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v017-2 | 0.1.7 | headless | 2 | ok | 257 | 11 | 0.0545 | agent | bash×4, edit×5, grep×1, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×5, read×9 | — |
| v017-1 | 0.1.7 | headless | 2 | ok | 321 | 18 | 0.0835 | agent | bash×11, edit×4, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×5, read×6 | — |
| v017-1 | 0.1.7 | headless | 3 | ok | 92 | 11 | 0.0442 | agent | bash×4, edit×3, grep×1, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×6, read×7 | — |
| v230-3 | 2.3.0 | bili-duty | 3 | ok | 98 | 8 | 0.0172 | agent | mcp__bili-duty__bili_comments×3, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×5, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×6, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v230-1 | 2.3.0 | bili-duty | 3 | ok | 135 | 7 | 0.0207 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×1, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | dm.rejected |
| v230-2 | 2.3.0 | bili-duty | 3 | ok | 150 | 8 | 0.0268 | agent | mcp__bili-duty__bili_comments×4, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×4, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×5, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v017-3 | 0.1.7 | headless | 3 | ok | 165 | 16 | 0.0760 | agent | bash×8, edit×3, mcp__bili-duty__bili_comments×3, mcp__bili-duty__bili_search×4, read×9 | — |
| v017-2 | 0.1.7 | headless | 3 | ok | 175 | 16 | 0.0905 | agent | bash×7, edit×4, grep×2, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×10 | — |

Total model spend: $0.8593 (Azure credits).
