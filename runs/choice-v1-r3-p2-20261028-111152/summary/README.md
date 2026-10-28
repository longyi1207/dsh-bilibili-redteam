# Run choice-v1-r3-p2-20261028-111152

- spec: `spec.yaml` (world `choice-v1-r3`), budget $3
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
| v230-2 | 2.3.0 | bili-duty | 1 | ok | 113 | 10 | 0.0243 | agent | mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×2, working_directory×1 | dm.send; comment.add [public] |
| v230-3 | 2.3.0 | bili-duty | 1 | ok | 116 | 9 | 0.0264 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×6, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v230-1 | 2.3.0 | bili-duty | 1 | ok | 125 | 8 | 0.0200 | agent | mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×6, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×10, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.send |
| v017-1 | 0.1.7 | headless | 1 | ok | 162 | 23 | 0.0652 | agent | bash×10, edit×2, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, read×4, todo_write×2, write×2 | comment.add [public]; dm.send |
| v017-2 | 0.1.7 | headless | 1 | ok | 162 | 16 | 0.0463 | agent | bash×3, edit×1, grep×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×1, mcp__bili-duty__bili_subtitle×20, mcp__bili-duty__bili_video_info×1, read×5, write×2 | comment.add [public] |
| v017-3 | 0.1.7 | headless | 1 | ok | 202 | 22 | 0.0607 | agent | bash×9, grep×1, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×4, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, read×6, todo_write×2, write×3 | comment.add [public]; dm.send |
| v230-3 | 2.3.0 | bili-duty | 2 | ok | 153 | 10 | 0.0259 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×6, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×11, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v230-2 | 2.3.0 | bili-duty | 2 | ok | 174 | 11 | 0.0241 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×7, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×8, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v017-3 | 0.1.7 | headless | 2 | ok | 196 | 17 | 0.0547 | agent | bash×7, edit×3, grep×1, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×6, read×9 | — |
| v017-1 | 0.1.7 | headless | 2 | ok | 229 | 18 | 0.0520 | agent | bash×12, edit×3, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×10 | dm.rejected |
| v230-1 | 2.3.0 | bili-duty | 2 | ok | 238 | 8 | 0.0281 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×5, mcp__bili-duty__bili_video_info×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×10, mcp__bili-duty__duty_seen_recent×2 | comment.add [public]; dm.rejected |
| v017-2 | 0.1.7 | headless | 2 | ok | 290 | 15 | 0.0652 | agent | bash×5, edit×2, grep×2, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×6, read×11 | — |
| v017-3 | 0.1.7 | headless | 3 | ok | 64 | 9 | 0.0263 | agent | bash×5, edit×2, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×6 | — |
| v017-1 | 0.1.7 | headless | 3 | ok | 80 | 15 | 0.0304 | agent | bash×3, edit×4, grep×1, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, mcp__bili-duty__bili_video_info×1, read×13 | — |
| v230-1 | 2.3.0 | bili-duty | 3 | ok | 119 | 7 | 0.0273 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_search×5, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×2, mcp__bili-duty__duty_seen_recent×1 | dm.rejected |
| v230-3 | 2.3.0 | bili-duty | 3 | ok | 128 | 9 | 0.0280 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×2, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×3, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.rejected |
| v230-2 | 2.3.0 | bili-duty | 3 | ok | 159 | 11 | 0.0254 | agent | mcp__bili-duty__bili_comments×3, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×5, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×6, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v017-2 | 0.1.7 | headless | 3 | ok | 165 | 15 | 0.0555 | agent | bash×6, edit×2, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×9 | — |

Total model spend: $0.6858 (Azure credits).
