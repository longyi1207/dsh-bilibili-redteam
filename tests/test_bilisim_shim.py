"""Simulator endpoints and platform rules, exercised through the `bilibili_api` shim (as mcp_server.py uses it).

The shim addresses Bilibili's real hostnames; here every request is redirected to an in-process test server.
"""
import json
from urllib.parse import urlsplit

import aiohttp
import pytest
from aiohttp.test_utils import TestServer

import bilibili_api
from bilibili_api import Credential, comment, homepage, search, session, user, video
from bilibili_api.exceptions import ArgsException, CredentialNoSessdataException, ResponseCodeException
from bili_sandbox.bilisim.app import BiliSim
from bili_sandbox.world.media import font_path
from bili_sandbox.world.spec import load_world
from bili_sandbox.world.store import WorldStore

from conftest import WORLD

assert bilibili_api.BILISANDBOX_SHIM


@pytest.fixture
async def sim(tmp_path, monkeypatch):
    world = load_world(WORLD)
    store = WorldStore(tmp_path / "world.db", world.policy, world.seed)
    store.seed_from(world, {})
    app = BiliSim(store, world, tmp_path / "media", "admintoken")
    server = TestServer(app.public_app())
    await server.start_server()
    original = aiohttp.ClientSession._request

    async def redirect(self, method, url, **kw):
        parts = urlsplit(str(url))
        headers = dict(kw.pop("headers", None) or {})
        headers["Host"] = parts.netloc
        local = str(server.make_url(parts.path)) + (f"?{parts.query}" if parts.query else "")
        return await original(self, method, local, headers=headers, **kw)

    monkeypatch.setattr(aiohttp.ClientSession, "_request", redirect)
    yield world, store
    await server.close()


def cred(store, handle):
    c = store.credentials(handle)
    return Credential(sessdata=c["sessdata"], bili_jct=c["bili_jct"], buvid3=c["buvid3"], dedeuserid=c["dedeuserid"])


async def test_video_info_subtitles_danmaku(sim):
    world, store = sim
    v = world.videos["cot"]
    vid = video.Video(bvid=v.bvid, credential=cred(store, "fish_a"))
    info = await vid.get_info()
    assert info["aid"] == v.aid and info["owner"]["name"] == "AI实验室小张" and info["stat"]["reply"] == 4
    assert info["pic"].startswith("http://i0.hdslb.com/bfs/archive/")
    sub = await vid.get_subtitle(cid=info["cid"])
    assert sub["subtitles"][0]["lan"] == "ai-zh"
    dms = await vid.get_danmakus(page_index=0)
    assert [d.text for d in dms][:2] == ["十一个！", "原来如此"] and dms[0].dm_time == 8.0
    with pytest.raises(CredentialNoSessdataException):
        await video.Video(bvid=v.bvid).get_subtitle(cid=info["cid"])
    with pytest.raises(ArgsException):
        video.Video(bvid="BV123")


async def test_unknown_video_is_minus_404(sim):
    with pytest.raises(ResponseCodeException) as e:
        await video.Video(bvid="BV1xx411c7mD").get_info()
    assert e.value.code == -404


async def test_search_highlight_and_feed(sim):
    world, store = sim
    res = await search.search_by_type("AI", search_type=search.SearchObjectType.VIDEO, order_type=search.OrderVideo.TOTALRANK)
    titles = [r["title"] for r in res["result"]]
    assert len(titles) == 5 and all('<em class="keyword">AI</em>' in t for t in titles[:2])
    feed = await homepage.get_videos(credential=cred(store, "fish_b"))
    assert feed["item"] and all(i["goto"] == "av" for i in feed["item"])


async def test_comment_post_review_queue_and_notifications(sim):
    world, store = sim
    v = world.videos["harness"]
    c = cred(store, "fish_a")
    res = await comment.send_comment("插件凭证那段讲得很实在，装之前确实该看看。", v.aid, comment.CommentResourceType.VIDEO, credential=c)
    assert res["rpid"] and res["root"] == 0
    page = await comment.get_comments(v.aid, comment.CommentResourceType.VIDEO, order=comment.OrderType.TIME)
    assert page["replies"][0]["content"]["message"].startswith("插件凭证")
    # a human replies to the agent's comment -> reply notification for the agent
    store.add_comment(store.account_by_sessdata(store.credentials("viewer_a")["sessdata"]), v.aid, "同意", res["rpid"], res["rpid"])
    replies = await session.get_replies(credential=c)
    assert replies["items"][0]["item"]["source_content"] == "同意"
    unread = await session.get_unread_messages(credential=c)
    assert unread["reply"] == 0  # get_replies marked them read
    # level-0 accounts go to review: not visible to others
    store.db.execute("UPDATE users SET level=0 WHERE handle='fish_b'")
    await comment.send_comment("新号评论", v.aid, comment.CommentResourceType.VIDEO, credential=cred(store, "fish_b"))
    public = await comment.get_comments(v.aid, comment.CommentResourceType.VIDEO, order=comment.OrderType.TIME)
    assert all(r["content"]["message"] != "新号评论" for r in public["replies"])
    kinds = [e["kind"] for e in store.events_since(0, 10000)]
    assert kinds.count("comment.add") == 2


async def test_dm_rules(sim):
    world, store = sim
    owner = world.users["owner_a"].mid
    c = cred(store, "fish_a")
    with pytest.raises(ResponseCodeException) as e:
        await session.send_msg(c, owner, session.EventType.TEXT, "长" * 501)
    assert e.value.code == 21007
    ok = await session.send_msg(c, owner, session.EventType.TEXT, "今天的日报好了")
    assert ok["msg_key"]
    stranger = world.users["viewer_c"].mid
    await session.send_msg(c, stranger, session.EventType.TEXT, "你好")
    with pytest.raises(ResponseCodeException) as e:
        await session.send_msg(c, stranger, session.EventType.TEXT, "在吗")
    assert e.value.code == 25003


async def test_user_space(sim):
    world, store = sim
    u = user.User(world.users["up_ailab"].mid, credential=cred(store, "fish_a"))
    info = await u.get_user_info()
    assert info["name"] == "AI实验室小张"
    vids = await u.get_videos()
    assert vids["page"]["count"] == 3
    rel = await u.get_relation_info()
    assert rel["follower"] == 128000


async def test_storyboard_and_cover(sim, tmp_path):
    try:
        font_path()
    except FileNotFoundError:
        pytest.skip("no CJK font on this machine")
    world, store = sim
    vid = video.Video(bvid=world.videos["cat_robot"].bvid)
    snap = await vid.get_video_snapshot(cid=world.videos["cat_robot"].cid, json_index=True, pvideo=False)
    assert snap["img_x_size"] == 480 and snap["index"][:3] == [0, 5, 10]
    async with aiohttp.ClientSession() as s:
        async with s.get("https:" + snap["image"][0]) as r:
            assert r.status == 200 and r.content_type == "image/jpeg"
        info = await vid.get_info()
        async with s.get(info["pic"].replace("http://", "https://") + "@512w.jpg") as r:
            assert r.status == 200
