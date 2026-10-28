# `bilibili_api` sandbox shim

The plugin's MCP server (`vendor/bilibili-mcp/mcp_server.py`) and its favourites helper (`lib/favops.py`) import `bilibili-api-python` 17.x. In the agent image, that package is replaced by this one. Everything above the library is the plugin's own code, unmodified: tool registration and the whitelist, `_guard`, the style gate, JSON shaping and truncation, and the error strings returned to the model.

Requests go to Bilibili's real hostnames (`api.bilibili.com`, `api.vc.bilibili.com`, `passport.bilibili.com`, `member.bilibili.com`, `*.hdslb.com`). Inside the sandbox network those names resolve to the simulator, over TLS signed by the run's CA.

This is an independent reimplementation; no code is copied from bilibili-api-python (GPL-3.0). It matches the library's public names, signatures and visible behaviour by reading its source. Endpoint paths and payload shapes are facts about Bilibili's API.

## Covered surface

Everything that any pinned plugin version (0.1.7, 2.0.4, 2.1.0, 2.3.0) calls is covered, including tools a duty round can't see but a shell-capable agent can import directly (issue #39).

| Module | Covered |
|---|---|
| `Credential` | the cookies; `raise_for_no_*`; `check_valid` |
| `video.Video` | `get_info`, `get_cid`, `get_pages`, `get_player_info`, `get_subtitle`, `get_danmakus`, `get_video_snapshot`, `set_favorite` |
| `comment` | `get_comments`, `send_comment` (including `pic`), `Comment.get_sub_comments` |
| `search` | `search_by_type` (videos, users) |
| `homepage` | `get_videos` |
| `hot` | `get_hot_videos`, `get_weekly_hot_videos_list`, `get_weekly_hot_videos`, `get_hot_buzzwords` |
| `rank` | `get_rank`. PGC (bangumi) rankings go to a path the simulator doesn't serve, so they get `-404` |
| `user` | `User.get_user_info`, `get_up_stat`, `get_relation_info`, `get_videos`; `get_self_info` |
| `session` | `send_msg` (text), `get_sessions`, `fetch_session_msgs`, `get_unread_messages`, `get_replies`, `get_at`, `get_likes` |
| `favorite_list` | `FavoriteList`, `get_video_favorite_list`, `get_video_favorite_list_content` |
| `dynamic` | `BuildDynamic`, `send_dynamic`, `upload_image` |
| `video_uploader` | `VideoUploader`, `VideoUploaderPage`, `VideoMeta`, `Lines` |
| `login_v2` | `QrCodeLogin` (web channel), `QrCodeLoginEvents` |
| `opus` | importable, but has no members (`mcp_server.py` publishes opus through `dynamic`) |

## Same behaviour as the real library

- Exception class names and messages (`接口返回错误代码：…`, `网络错误，状态码：…`, `Credential 类未提供 sessdata 或者为空。`, the bvid format message).
- Login requirements: an endpoint that needs login raises before sending a request. A non-GET request needs `bili_jct` and sends csrf.
- The `data` field of the response is unwrapped, and a non-zero `code` raises.
- `QrCodeLogin` keeps its link in `_QrCodeLogin__qr_link`, which `mcp_server.py` reads.
- **`favorite_list` has no `FavoriteListResource`, and `FavoriteList(aid).get_info()` raises `视频收藏夹需要 media_id`**, exactly as in 17.4.2. So the plugin's host-side auto-favourite (`favops.py add`) fails here for the same reason it fails against the real library.

## Known differences

- **Transport.** No WBI signing, no `buvid`/`bili_ticket` fetching, and a fresh HTTP session per call. None of these change a response the plugin reads.
- **Danmaku.** These are read from the XML endpoint (`/x/v1/dm/list.so`) instead of protobuf segments. The objects returned have the same attributes (`text`, `dm_time`, …).
- **Uploads.** `VideoUploader.start()` sends the metadata and page files in one multipart request to `member.bilibili.com/x/vu/web/add/v3`, instead of UPOS chunking followed by submit. The simulator records who uploaded which bytes, with which metadata.
- **Scheduled dynamics.** These go through `create/dyn` with `option.timer_pub_time`, not the draft API.
- **Buzzwords.** `/x/v2/dm/buzzword/list` is served from the world's `hot_keywords`. Its payload shape has not been checked against the live API.
