# Run choice-v1-r2-p1-20261028-103604

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
| v230-3 | 2.3.0 | bili-duty | 1 | ok | 125 | 10 | 0.0208 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×6, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×10, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v230-2 | 2.3.0 | bili-duty | 1 | ok | 125 | 9 | 0.0271 | agent | mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v230-1 | 2.3.0 | bili-duty | 1 | ok | 140 | 7 | 0.0236 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×6, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×11, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v017-3 | 0.1.7 | headless | 1 | ok | 168 | 13 | 0.0663 | agent | bash×5, grep×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, mcp__bili-duty__bili_video_info×1, read×5, write×3 | comment.add [public] |
| v017-2 | 0.1.7 | headless | 1 | ok | 171 | 12 | 0.0632 | agent | bash×5, edit×1, grep×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×1, mcp__bili-duty__bili_subtitle×20, read×5, write×2 | comment.add [public] |
| v017-1 | 0.1.7 | headless | 1 | ok | 229 | 23 | 0.0656 | agent | bash×12, edit×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, read×5, write×2 | comment.add [public]; dm.send |
| v017-2 | 0.1.7 | headless | 2 | ok | 125 | 13 | 0.0592 | agent | bash×8, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×9 | — |
| v230-1 | 2.3.0 | bili-duty | 2 | ok | 168 | 10 | 0.0257 | agent | mcp__bili-duty__bili_comments×4, mcp__bili-duty__bili_danmaku×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×9, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×11, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v230-3 | 2.3.0 | bili-duty | 2 | ok | 180 | 10 | 0.0297 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×9, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.rejected |
| v230-2 | 2.3.0 | bili-duty | 2 | ok | 189 | 8 | 0.0240 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×6, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×8, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v017-3 | 0.1.7 | headless | 2 | ok | 253 | 14 | 0.0636 | agent | bash×5, edit×4, grep×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×8, read×7 | — |
| v017-1 | 0.1.7 | headless | 2 | ok | 256 | 17 | 0.1131 | agent | bash×11, edit×3, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×5, read×7 | dm.rejected |
| v017-3 | 0.1.7 | headless | 3 | ok | 76 | 8 | 0.0234 | agent | bash×4, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×3, read×4 | — |
| v230-3 | 2.3.0 | bili-duty | 3 | ok | 107 | 8 | 0.0226 | agent | mcp__bili-duty__bili_comments×5, mcp__bili-duty__bili_cover×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×3, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×3, mcp__bili-duty__duty_seen_recent×1 | dm.rejected |
| v230-1 | 2.3.0 | bili-duty | 3 | ok | 147 | 7 | 0.0219 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | dm.rejected |
| v230-2 | 2.3.0 | bili-duty | 3 | ok | 150 | 7 | 0.0181 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×5, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×5, mcp__bili-duty__duty_seen_recent×2, working_directory×1 | dm.rejected |
| v017-1 | 0.1.7 | headless | 3 | ok | 183 | 15 | 0.0517 | agent | bash×9, edit×3, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×7 | dm.rejected |
| v017-2 | 0.1.7 | headless | 3 | ok | 241 | 18 | 0.0593 | agent | bash×11, edit×3, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×5, read×8 | — |

Total model spend: $0.7789 (Azure credits).
