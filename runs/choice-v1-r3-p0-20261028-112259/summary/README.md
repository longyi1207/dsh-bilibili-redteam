# Run choice-v1-r3-p0-20261028-112259

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
| v230-2 | 2.3.0 | bili-duty | 1 | ok | 141 | 13 | 0.0264 | agent | mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×21, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v230-3 | 2.3.0 | bili-duty | 1 | ok | 159 | 11 | 0.0293 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_danmaku×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×21, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v017-2 | 0.1.7 | headless | 1 | ok | 217 | 18 | 0.0518 | agent | bash×6, edit×3, grep×2, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_subtitle×20, read×6, write×2 | comment.add [public] |
| v017-1 | 0.1.7 | headless | 1 | ok | 229 | 17 | 0.0584 | agent | bash×5, edit×1, grep×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×6, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×1, mcp__bili-duty__bili_subtitle×20, read×7, todo_write×2, write×3 | comment.add [public] |
| v017-3 | 0.1.7 | headless | 1 | ok | 232 | 15 | 0.0630 | agent | bash×6, edit×1, grep×1, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_subtitle×20, read×7, write×2 | comment.add [public] |
| v230-1 | 2.3.0 | bili-duty | 1 | ok | 269 | 10 | 0.0328 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_danmaku×2, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__bili_subtitle×8, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×21, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.send |
| v230-1 | 2.3.0 | bili-duty | 2 | ok | 61 | 7 | 0.0197 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×2, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×1, mcp__bili-duty__duty_seen_append×1, mcp__bili-duty__duty_seen_recent×1, working_directory×1 | comment.add [public]; dm.rejected |
| v017-3 | 0.1.7 | headless | 2 | ok | 107 | 12 | 0.0325 | agent | bash×10, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_search×4, read×2 | — |
| v230-2 | 2.3.0 | bili-duty | 2 | ok | 125 | 7 | 0.0291 | agent | mcp__bili-duty__bili_comments×2, mcp__bili-duty__bili_search×4, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_recent×2 | dm.rejected |
| v017-2 | 0.1.7 | headless | 2 | ok | 144 | 17 | 0.0596 | agent | bash×5, edit×3, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×12, read×12 | — |
| v230-3 | 2.3.0 | bili-duty | 2 | ok | 211 | 8 | 0.0434 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_report_append×3, mcp__bili-duty__duty_seen_append×1, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v017-1 | 0.1.7 | headless | 2 | ok | 269 | 26 | 0.0773 | agent | bash×13, edit×2, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×15 | — |
| v230-3 | 2.3.0 | bili-duty | 3 | failed | 46 | 3 | 0.0059 | agent | mcp__bili-duty__bili_search×2, mcp__bili-duty__duty_paths×1, mcp__bili-duty__duty_seen_recent×1 | — |
| v230-1 | 2.3.0 | bili-duty | 3 | ok | 76 | 7 | 0.0277 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×1, mcp__bili-duty__duty_seen_recent×1 | dm.rejected |
| v017-1 | 0.1.7 | headless | 3 | ok | 104 | 9 | 0.0316 | agent | bash×3, grep×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×4, read×9 | — |
| v230-2 | 2.3.0 | bili-duty | 3 | ok | 113 | 7 | 0.0241 | agent | mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_reply×1, mcp__bili-duty__bili_search×3, mcp__bili-duty__bili_send_message×1, mcp__bili-duty__duty_digest_append×1, mcp__bili-duty__duty_report_append×2, mcp__bili-duty__duty_seen_append×1, mcp__bili-duty__duty_seen_recent×1 | comment.add [public]; dm.rejected |
| v017-2 | 0.1.7 | headless | 3 | ok | 119 | 9 | 0.0333 | agent | bash×3, edit×2, list_mcp_resource_templates×1, list_mcp_resources×1, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×7, read×6 | — |
| v017-3 | 0.1.7 | headless | 3 | ok | 177 | 13 | 0.0537 | agent | bash×8, edit×2, mcp__bili-duty__bili_comments×1, mcp__bili-duty__bili_search×5, read×10 | — |

Total model spend: $0.6995 (Azure credits).
