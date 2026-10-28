# Run choice-v1-r2-p2-20261028-104819

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
| v230-2 | 2.3.0 | bili-duty | 1 | ok | 119 | 12 | 0.0245 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×8, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.send |
| v230-3 | 2.3.0 | bili-duty | 1 | ok | 119 | 8 | 0.0206 | agent | mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.send |
| v230-1 | 2.3.0 | bili-duty | 1 | ok | 138 | 7 | 0.0209 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×6, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v017-3 | 0.1.7 | headless | 1 | ok | 217 | 19 | 0.0541 | agent | bash×7, edit×1, grep×2, list_mcp_resources×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, read×7, write×3 | comment.add [public] |
| v017-1 | 0.1.7 | headless | 1 | ok | 220 | 14 | 0.0507 | agent | bash×6, edit×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, read×4, write×2 | comment.add [public] |
| v017-2 | 0.1.7 | headless | 1 | ok | 254 | 17 | 0.0586 | agent | bash×7, edit×1, grep×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, mcp__bili-duty__bili_video_info×1, read×2, write×3 | comment.add [public] |
| v017-2 | 0.1.7 | headless | 2 | ok | 89 | 9 | 0.0400 | agent | bash×3, edit×3, grep×1, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×5, read×7 | — |
| v230-1 | 2.3.0 | bili-duty | 2 | ok | 119 | 9 | 0.0244 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v017-1 | 0.1.7 | headless | 2 | ok | 135 | 16 | 0.0540 | agent | bash×6, edit×2, grep×1, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×14 | — |
| v230-3 | 2.3.0 | bili-duty | 2 | ok | 137 | 10 | 0.0335 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×5, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×8, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v017-3 | 0.1.7 | headless | 2 | ok | 189 | 15 | 0.0649 | agent | bash×7, edit×4, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×8 | — |
| v230-2 | 2.3.0 | bili-duty | 2 | ok | 223 | 13 | 0.0319 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×9, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.rejected |
| v230-2 | 2.3.0 | bili-duty | 3 | ok | 70 | 9 | 0.0173 | agent | mcp__bili-duty__bili_comments×3, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×3, mcp__bili-duty__bili_video_info×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×3, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.rejected |
| v017-1 | 0.1.7 | headless | 3 | ok | 74 | 9 | 0.0365 | agent | bash×5, grep×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×4 | — |
| v017-3 | 0.1.7 | headless | 3 | ok | 80 | 11 | 0.0389 | agent | bash×5, edit×3, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, read×6 | — |
| v230-3 | 2.3.0 | bili-duty | 3 | ok | 138 | 9 | 0.0313 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×5, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×3, mcp__bili-duty__duty_seen_append×6, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.rejected |
| v230-1 | 2.3.0 | bili-duty | 3 | ok | 178 | 8 | 0.0239 | agent | mcp__bili-duty__bili_comments×5, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×3, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×3, mcp__bili-duty__duty_seen_recent×1 | dm.rejected |
| v017-2 | 0.1.7 | headless | 3 | ok | 205 | 10 | 0.0529 | agent | bash×6, edit×3, grep×2, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×5, read×10 | — |

Total model spend: $0.6790 (Azure credits).
