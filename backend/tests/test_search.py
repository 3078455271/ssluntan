from typing import Any

from httpx import AsyncClient


async def search(client: AsyncClient, **params: Any) -> dict[str, Any]:
    response = await client.get("/api/search", params=params)
    assert response.status_code == 200, response.text
    return response.json()


async def test_title_match_ranks_before_content_match(
    client: AsyncClient, forum: dict[str, Any]
) -> None:
    payload = await search(client, q="fastapi")

    assert payload["total"] == 2
    first, second = payload["items"]
    assert first["topic"]["id"] == forum["title_topic"]
    assert first["match"] == {
        "matched_in": "title",
        "post_id": None,
        "floor": None,
        "snippet": None,
    }
    assert second["topic"]["id"] == forum["content_topic"]

    match = second["match"]
    assert match["matched_in"] == "content"
    assert match["floor"] == 3
    assert match["post_id"] is not None
    assert "fastapi" in match["snippet"].casefold()


async def test_content_match_uses_earliest_matching_floor(
    client: AsyncClient, forum: dict[str, Any]
) -> None:
    payload = await search(client, q="依赖注入")

    assert payload["total"] == 1
    hit = payload["items"][0]
    assert hit["topic"]["id"] == forum["content_topic"]
    assert hit["match"]["floor"] == 4
    assert "依赖注入" in hit["match"]["snippet"]


async def test_inactive_board_is_excluded_from_search(
    client: AsyncClient, forum: dict[str, Any]
) -> None:
    payload = await search(client, q="隐藏内容")

    assert payload["total"] == 0
    assert payload["items"] == []


async def test_board_filter_limits_results(
    client: AsyncClient, forum: dict[str, Any]
) -> None:
    general = await search(client, q="fastapi", board_id=forum["board_general"])
    hidden = await search(client, q="fastapi", board_id=forum["board_hidden"])

    assert general["total"] == 2
    assert {hit["topic"]["id"] for hit in general["items"]} == {
        forum["title_topic"],
        forum["content_topic"],
    }
    assert hidden["total"] == 0


async def test_like_wildcards_are_matched_literally(
    client: AsyncClient, forum: dict[str, Any]
) -> None:
    percent = await search(client, q="100%")
    underscore = await search(client, q="a_b")

    assert percent["total"] == 1
    assert percent["items"][0]["topic"]["id"] == forum["percent_topic"]

    assert underscore["total"] == 1
    assert underscore["items"][0]["topic"]["id"] == forum["underscore_topic"]


async def test_latest_sort_uses_last_activity(
    client: AsyncClient, forum: dict[str, Any]
) -> None:
    payload = await search(client, q="fastapi", sort="latest")

    assert [hit["topic"]["id"] for hit in payload["items"]] == [
        forum["content_topic"],
        forum["title_topic"],
    ]


async def test_search_pagination_reports_totals(
    client: AsyncClient, forum: dict[str, Any]
) -> None:
    payload = await search(client, q="fastapi", page=2, page_size=1)

    assert payload["total"] == 2
    assert payload["page"] == 2
    assert payload["pages"] == 2
    assert len(payload["items"]) == 1
    assert payload["items"][0]["topic"]["id"] == forum["content_topic"]


async def test_short_keywords_are_rejected(client: AsyncClient) -> None:
    too_short = await client.get("/api/search", params={"q": "a"})
    whitespace_only = await client.get("/api/search", params={"q": "  a  "})

    assert too_short.status_code == 422
    assert whitespace_only.status_code == 422
    assert "至少" in whitespace_only.json()["detail"]
