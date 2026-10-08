from tests.conftest import register_and_login


def make_app(client, headers, **overrides):
    payload = {
        "company": "Takealot",
        "position": "Junior Python Developer",
        "location": "Cape Town",
        "job_url": "https://example.com/jobs/123",
        "status": "applied",
        "applied_on": "2026-10-01",
    } | overrides
    res = client.post("/applications", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


def test_create_and_get(client, auth_headers):
    created = make_app(client, auth_headers)
    assert created["company"] == "Takealot"
    assert created["applied_on"] == "2026-10-01"
    assert created["job_url"] == "https://example.com/jobs/123"

    res = client.get(f"/applications/{created['id']}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["position"] == "Junior Python Developer"


def test_create_validates_fields(client, auth_headers):
    res = client.post(
        "/applications",
        json={"company": "", "position": "Dev", "status": "dreaming"},
        headers=auth_headers,
    )
    assert res.status_code == 422


def test_list_with_filter_search_and_pagination(client, auth_headers):
    make_app(client, auth_headers, company="Takealot", status="applied")
    make_app(
        client, auth_headers, company="Capitec", position="Backend Engineer", status="interviewing"
    )
    make_app(client, auth_headers, company="Discovery", status="rejected")

    res = client.get("/applications", headers=auth_headers)
    assert res.json()["total"] == 3

    res = client.get("/applications?status=interviewing", headers=auth_headers)
    assert [a["company"] for a in res.json()["items"]] == ["Capitec"]

    res = client.get("/applications?q=backend", headers=auth_headers)
    assert res.json()["total"] == 1

    res = client.get("/applications?sort=company&order=asc&limit=2", headers=auth_headers)
    body = res.json()
    assert body["total"] == 3
    assert [a["company"] for a in body["items"]] == ["Capitec", "Discovery"]

    res = client.get("/applications?sort=company&order=asc&limit=2&offset=2", headers=auth_headers)
    assert [a["company"] for a in res.json()["items"]] == ["Takealot"]


def test_partial_update(client, auth_headers):
    created = make_app(client, auth_headers)
    res = client.patch(
        f"/applications/{created['id']}",
        json={"status": "interviewing", "notes": "First round on Friday"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "interviewing"
    assert body["notes"] == "First round on Friday"
    assert body["company"] == "Takealot"  # untouched fields stay the same


def test_delete(client, auth_headers):
    created = make_app(client, auth_headers)
    res = client.delete(f"/applications/{created['id']}", headers=auth_headers)
    assert res.status_code == 204
    assert client.get(f"/applications/{created['id']}", headers=auth_headers).status_code == 404


def test_missing_application_returns_404(client, auth_headers):
    assert client.get("/applications/999", headers=auth_headers).status_code == 404


def test_users_cannot_see_each_others_applications(client, auth_headers):
    mine = make_app(client, auth_headers)
    other = register_and_login(client, email="other@example.com")

    assert client.get(f"/applications/{mine['id']}", headers=other).status_code == 404
    assert (
        client.patch(
            f"/applications/{mine['id']}", json={"status": "offer"}, headers=other
        ).status_code
        == 404
    )
    assert client.delete(f"/applications/{mine['id']}", headers=other).status_code == 404
    assert client.get("/applications", headers=other).json()["total"] == 0


def test_stats(client, auth_headers):
    make_app(client, auth_headers, status="wishlist")
    make_app(client, auth_headers, status="applied")
    make_app(client, auth_headers, status="applied")
    make_app(client, auth_headers, status="interviewing")
    make_app(client, auth_headers, status="rejected")

    res = client.get("/applications/stats", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 5
    assert body["by_status"]["applied"] == 2
    assert body["by_status"]["offer"] == 0
    # 4 submitted (wishlist excluded), 2 got a reply
    assert body["response_rate"] == 0.5


def test_stats_with_no_applications(client, auth_headers):
    body = client.get("/applications/stats", headers=auth_headers).json()
    assert body["total"] == 0
    assert body["response_rate"] == 0.0
