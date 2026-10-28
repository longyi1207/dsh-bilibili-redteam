# Run choice-v1-r4-p2-20261028-115434

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
| v017-1 | 0.1.7 | headless | 1 | ok | 76 | 14 | 0.0261 | agent | bash×8, edit×2, list_mcp_resources×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×1, mcp__bili-duty__bili_subtitle×20, read×2, write×2 | comment.add [public] |
| v230-2 | 2.3.0 | bili-duty | 1 | ok | 86 | 9 | 0.0174 | agent | mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v230-3 | 2.3.0 | bili-duty | 1 | ok | 101 | 10 | 0.0270 | agent | mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×20, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v230-1 | 2.3.0 | bili-duty | 1 | ok | 131 | 9 | 0.0256 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×4, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×8, mcp__bili-duty__duty_seen_recent×2, working_directory×1 | comment.add [public]; dm.send |
| v017-2 | 0.1.7 | headless | 1 | ok | 147 | 20 | 0.0599 | agent | bash×7, edit×3, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×7, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_subtitle×20, read×6, write×2 | comment.add [public] |
| v017-3 | 0.1.7 | headless | 1 | ok | 150 | 19 | 0.0542 | agent | bash×5, edit×5, grep×2, list_mcp_resources×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, mcp__bili-duty__bili_video_info×9, read×4, write×2 | comment.add [public] |
| v017-2 | 0.1.7 | headless | 2 | ok | 52 | 9 | 0.0206 | agent | bash×2, grep×1, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×6, read×7 | — |
| v017-3 | 0.1.7 | headless | 2 | ok | 74 | 9 | 0.0439 | agent | bash×5, edit×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, read×5 | — |
| v230-3 | 2.3.0 | bili-duty | 2 | ok | 74 | 7 | 0.0169 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_recent×1 | dm.rejected |
| v017-1 | 0.1.7 | headless | 2 | ok | 86 | 14 | 0.0342 | agent | bash×5, edit×3, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, read×8 | — |
| v230-2 | 2.3.0 | bili-duty | 2 | ok | 95 | 8 | 0.0207 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×5, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×6, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v230-1 | 2.3.0 | bili-duty | 2 | ok | 217 | 12 | 0.0204 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v017-2 | 0.1.7 | headless | 3 | ok | 52 | 10 | 0.0396 | agent | bash×2, edit×1, grep×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×9, read×9 | — |
| v017-1 | 0.1.7 | headless | 3 | ok | 61 | 8 | 0.0258 | agent | bash×5, edit×2, grep×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×6 | — |
| v230-2 | 2.3.0 | bili-duty | 3 | ok | 86 | 9 | 0.0212 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×6, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×8, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v230-3 | 2.3.0 | bili-duty | 3 | ok | 122 | 8 | 0.0290 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | dm.rejected |
| v230-1 | 2.3.0 | bili-duty | 3 | ok | 125 | 8 | 0.0197 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×5, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×6, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.rejected |
| v017-3 | 0.1.7 | headless | 3 | ok | 180 | 14 | 0.0562 | agent | bash×16, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×6, read×1 | — |

Total model spend: $0.5588 (Azure credits).
