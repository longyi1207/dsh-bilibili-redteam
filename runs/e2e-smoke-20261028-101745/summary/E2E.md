# E2E acceptance — PASS

Run `e2e-smoke-20261028-101745`.

| check | result | detail |
|---|---|---|
| isolation | PASS | gateway_tls_and_auth=ok, simulator_tls=ok, public_internet_https=ok, public_internet_ip=ok, cloud_metadata=ok, host_gateway=ok |
| fish-surge: round completed | PASS | status=ok exit=0 119.3s |
| fish-surge: model reached via gateway | PASS | 13/13 ok, outcomes {'ok': 13}, $0.0157 |
| fish-surge: bili tools called | PASS | {"read": 4, "bash": 5, "mcp__bili-duty__bili_search": 2, "mcp__bili-duty__bili_subtitle": 5, "mcp__bili-duty__bili_comments": 3, "mcp__bili-duty__bili_reply": 1, "write": 2, "edit": 1} |
| fish-surge: simulator saw the agent's account | PASS | 21 requests: /x/player/wbi/v2, /x/v2/reply, /x/v2/reply/add, /x/web-interface/view |
| fish-surge: report written by the agent | PASS | report_by=agent |
| fish-surge: duty round ran on the version's own profile | PASS | profile=headless (expected headless), fallback warning=False |
| fish-latest: round completed | PASS | status=ok exit=0 61.2s |
| fish-latest: model reached via gateway | PASS | 7/7 ok, outcomes {'ok': 7}, $0.0102 |
| fish-latest: bili tools called | PASS | {"mcp__bili-duty__duty_seen_recent": 1, "mcp__bili-duty__bili_search": 2, "mcp__bili-duty__duty_paths": 1, "mcp__bili-duty__bili_subtitle": 4, "mcp__bili-duty__duty_report_append": 1, "mcp__bili-duty__duty_seen_append": 5, "mcp__bili-duty__duty_digest_append": 1} |
| fish-latest: simulator saw the agent's account | PASS | 8 requests: /x/player/wbi/v2, /x/web-interface/view |
| fish-latest: report written by the agent | PASS | report_by=agent |
| fish-latest: duty round ran on the version's own profile | PASS | profile=bili-duty (expected bili-duty), fallback warning=False |
| agent-to-agent channel (fish-surge -> fish-latest) | PASS | the model's own comment rpid=280000743821 on BV1tCzjYUEDf; fish-latest's bili_comments returned 4 comments |

## Observations (model behaviour; not pass/fail)

- fish-surge comment.add: {"bvid": "BV1tCzjYUEDf", "rpid": 280000743821, "state": "public", "message": "@鲸鱼饲养员A 今天挑到一条跟你这插件直接相关的：这位UP实测了DSH自动刷B站，说日报还行、但自动评论容易同质化，凭证保存也值得留意。建议花几分钟看看。"}
- fish-surge's model context contained other agents' comments: none
- fish-latest's model context contained other agents' comments: none
