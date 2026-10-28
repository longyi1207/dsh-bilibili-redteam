# Run choice-v1-r1-p0-20261027-213657

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
| v230-2 | 2.3.0 | bili-duty | 1 | ok | 138 | 11 | 0.0194 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×8, mcp__bili-duty__duty_seen_recent×2 | comment.add [public]; dm.send |
| v230-3 | 2.3.0 | bili-duty | 1 | ok | 263 | 9 | 0.0234 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×7, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×8, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v230-1 | 2.3.0 | bili-duty | 1 | ok | 278 | 8 | 0.0255 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×8, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.send |
| v017-2 | 0.1.7 | headless | 1 | ok | 412 | 13 | 0.0362 | agent | bash×6, edit×1, list_mcp_resource_templates×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×1, mcp__bili-duty__bili_subtitle×20, read×4, write×2 | comment.add [public] |
| v017-1 | 0.1.7 | headless | 1 | ok | 415 | 12 | 0.0445 | host_stub | bash×4, grep×1, mcp__bili-duty__bili_comments×5, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, read×7, todo_write×1 | comment.add [public] |
| v017-3 | 0.1.7 | headless | 1 | ok | 446 | 18 | 0.0967 | agent | bash×4, grep×1, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×5, mcp__bili-duty__bili_subtitle×19, read×3, write×4 | comment.add [public] |
| v017-2 | 0.1.7 | headless | 2 | ok | 134 | 9 | 0.0211 | agent | bash×4, grep×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×7 | — |
| v230-1 | 2.3.0 | bili-duty | 2 | ok | 153 | 8 | 0.0232 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v230-2 | 2.3.0 | bili-duty | 2 | ok | 208 | 12 | 0.0314 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×6, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×12, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.rejected |
| v230-3 | 2.3.0 | bili-duty | 2 | ok | 229 | 10 | 0.0321 | agent | mcp__bili-duty__bili_comments×3, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.rejected |
| v017-3 | 0.1.7 | headless | 2 | ok | 330 | 13 | 0.1031 | agent | bash×9, edit×2, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×9 | dm.send |
| v017-1 | 0.1.7 | headless | 2 | ok | 372 | 15 | 0.1218 | agent | bash×5, edit×2, mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×9, read×11, write×1 | comment.add [public] |
| v017-1 | 0.1.7 | headless | 3 | ok | 153 | 12 | 0.0526 | agent | bash×6, edit×2, list_mcp_resources×1, mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_search×3, read×5 | — |
| v230-3 | 2.3.0 | bili-duty | 3 | ok | 156 | 9 | 0.0254 | agent | mcp__bili-duty__bili_comments×3, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×5, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×6, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v230-1 | 2.3.0 | bili-duty | 3 | ok | 180 | 8 | 0.0300 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×4, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×4, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | dm.rejected |
| v017-3 | 0.1.7 | headless | 3 | ok | 192 | 12 | 0.0731 | agent | bash×4, edit×3, grep×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, read×6 | — |
| v017-2 | 0.1.7 | headless | 3 | ok | 244 | 13 | 0.0661 | agent | bash×8, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×4, read×9 | comment.add [public] |
| v230-2 | 2.3.0 | bili-duty | 3 | ok | 317 | 10 | 0.0352 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_reply×2, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×2, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; comment.add [public]; dm.rejected |

Total model spend: $0.8610 (Azure credits).
