import requests
import time
import os
import pytest

from .conftest import API_PREFIX

crawl_id = None


def get_crawl(org_id, auth_headers, crawl_id):
    r = requests.get(
        f"{API_PREFIX}/orgs/{org_id}/crawls/{crawl_id}/replay.json",
        headers=auth_headers,
    )
    assert r.status_code == 200
    return r.json()


def test_start_crawl_to_cancel(
    default_org_id, crawler_config_id_only, crawler_auth_headers
):
    r = requests.post(
        f"{API_PREFIX}/orgs/{default_org_id}/crawlconfigs/{crawler_config_id_only}/run",
        headers=crawler_auth_headers,
    )
    assert r.status_code == 200
    data = r.json()

    assert data.get("started")

    global crawl_id
    crawl_id = data["started"]


def test_cancel_crawl(default_org_id, crawler_auth_headers):
    data = get_crawl(default_org_id, crawler_auth_headers, crawl_id)
    while data["state"] == "starting":
        time.sleep(5)
        data = get_crawl(default_org_id, crawler_auth_headers, crawl_id)

    r = requests.post(
        f"{API_PREFIX}/orgs/{default_org_id}/crawls/{crawl_id}/cancel",
        headers=crawler_auth_headers,
    )
    data = r.json()
    assert data["success"] == True

    data = get_crawl(default_org_id, crawler_auth_headers, crawl_id)

    while data["state"] == "running":
        data = get_crawl(default_org_id, crawler_auth_headers, crawl_id)

    assert data["state"] == "canceled"
    assert data["stopping"] == False

    assert len(data["resources"]) == 0


@pytest.mark.skipif(os.environ.get("CI") is not None, reason="Skip Test on CI")
def test_start_crawl_to_stop(
    default_org_id, crawler_config_id_only, crawler_auth_headers
):
    r = requests.post(
        f"{API_PREFIX}/orgs/{default_org_id}/crawlconfigs/{crawler_config_id_only}/run",
        headers=crawler_auth_headers,
    )
    assert r.status_code == 200
    data = r.json()

    assert data.get("started")

    global crawl_id
    crawl_id = data["started"]


@pytest.mark.skipif(os.environ.get("CI") is not None, reason="Skip Test on CI")
def test_stop_crawl(default_org_id, crawler_config_id_only, crawler_auth_headers):
    data = get_crawl(default_org_id, crawler_auth_headers, crawl_id)
    while data["state"] == "starting":
        time.sleep(5)
        data = get_crawl(default_org_id, crawler_auth_headers, crawl_id)

    r = requests.post(
        f"{API_PREFIX}/orgs/{default_org_id}/crawls/{crawl_id}/stop",
        headers=crawler_auth_headers,
    )
    data = r.json()
    assert data["success"] == True

    # test crawl
    data = get_crawl(default_org_id, crawler_auth_headers, crawl_id)
    assert data["stopping"] == True

    # test workflow
    r = requests.get(
        f"{API_PREFIX}/orgs/{default_org_id}/crawlconfigs/{crawler_config_id_only}",
        headers=crawler_auth_headers,
    )
    assert r.json()["currCrawlStopping"] == True

    while data["state"] == "running":
        data = get_crawl(default_org_id, crawler_auth_headers, crawl_id)

    assert data["state"] == "partial_complete"
    assert data["stopping"] == True

    assert len(data["resources"]) == 1