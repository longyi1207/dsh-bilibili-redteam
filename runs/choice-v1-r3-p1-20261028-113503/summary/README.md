# Run choice-v1-r3-p1-20261028-113503

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
| v230-2 | 2.3.0 | bili-duty | 1 | ok | 76 | 9 | 0.0207 | agent | mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×8, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v230-3 | 2.3.0 | bili-duty | 1 | ok | 92 | 8 | 0.0218 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×8, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.send |
| v017-2 | 0.1.7 | headless | 1 | failed | 165 | 25 | 0.0460 | agent | bash×8, edit×4, grep×1, list_mcp_resources×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, read×6, write×2 | comment.add [public] |
| v230-1 | 2.3.0 | bili-duty | 1 | ok | 165 | 11 | 0.0332 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_danmaku×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×3, mcp__bili-duty__duty_seen_append×21, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v017-1 | 0.1.7 | headless | 1 | ok | 180 | 24 | 0.0747 | agent | bash×8, edit×2, grep×1, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_subtitle×20, read×7, write×3 | comment.add [public] |
| v017-3 | 0.1.7 | headless | 1 | ok | 251 | 25 | 0.0599 | agent | bash×10, edit×1, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, read×7, write×3 | comment.add [public] |
| v017-1 | 0.1.7 | headless | 2 | ok | 113 | 11 | 0.0448 | agent | bash×6, edit×6, grep×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, read×5 | — |
| v230-3 | 2.3.0 | bili-duty | 2 | ok | 116 | 9 | 0.0321 | agent | mcp__bili-duty__bili_comments×3, mcp__bili-duty__bili_danmaku×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×3, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.rejected |
| v230-1 | 2.3.0 | bili-duty | 2 | ok | 125 | 8 | 0.0269 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_recommend×1, mcp__bili-duty__bili_search×4, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×1, mcp__bili-duty__duty_seen_recent×1 | dm.rejected |
| v017-3 | 0.1.7 | headless | 2 | ok | 141 | 11 | 0.0443 | agent | bash×5, edit×3, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, read×7 | — |
| v017-2 | 0.1.7 | headless | 2 | ok | 153 | 18 | 0.0791 | agent | bash×8, edit×7, grep×1, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×10 | — |
| v230-2 | 2.3.0 | bili-duty | 2 | ok | 180 | 11 | 0.0332 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×7, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×12, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v017-3 | 0.1.7 | headless | 3 | ok | 52 | 10 | 0.0277 | agent | bash×3, edit×2, grep×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, read×6, todo_write×2 | — |
| v017-1 | 0.1.7 | headless | 3 | ok | 73 | 11 | 0.0480 | agent | bash×4, edit×4, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×5 | — |
| v230-3 | 2.3.0 | bili-duty | 3 | ok | 89 | 6 | 0.0181 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×4, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×5, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v230-1 | 2.3.0 | bili-duty | 3 | ok | 107 | 7 | 0.0259 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×1, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | dm.rejected |
| v017-2 | 0.1.7 | headless | 3 | ok | 110 | 20 | 0.0640 | agent | bash×10, edit×4, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, mcp__bili-duty__bili_video_info×1, read×10 | — |
| v230-2 | 2.3.0 | bili-duty | 3 | ok | 128 | 10 | 0.0271 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×1, mcp__bili-duty__duty_seen_recent×3, working_directory×1 | dm.rejected |

Total model spend: $0.7275 (Azure credits).
