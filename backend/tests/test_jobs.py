def test_list_jobs_requires_auth(client):
    assert client.get("/api/jobs").status_code == 401


def test_create_job_requires_auth(client):
    resp = client.post("/api/jobs", json={"code": "J1", "name": "测试", "location": "厦门"})
    assert resp.status_code == 401


def test_list_jobs_returns_seed_job(client, auth_headers):
    resp = client.get("/api/jobs", headers=auth_headers)
    assert resp.status_code == 200
    codes = [j["code"] for j in resp.json()]
    assert "DEMO-JOB-001" in codes


def test_create_job_success(client, auth_headers):
    resp = client.post(
        "/api/jobs",
        json={"code": "JOB-100", "name": "测试工程师", "location": "北京"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "JOB-100"
    assert data["name"] == "测试工程师"
    assert data["location"] == "北京"
    assert data["is_active"] is True


def test_create_job_duplicate_code_returns_400(client, auth_headers):
    payload = {"code": "DUP-1", "name": "重复", "location": "上海"}
    assert client.post("/api/jobs", json=payload, headers=auth_headers).status_code == 201
    assert client.post("/api/jobs", json=payload, headers=auth_headers).status_code == 400


def test_update_job(client, auth_headers):
    created = client.post(
        "/api/jobs",
        json={"code": "JOB-200", "name": "原名称", "location": "广州"},
        headers=auth_headers,
    ).json()
    resp = client.put(
        f"/api/jobs/{created['id']}",
        json={"name": "新名称", "location": "深圳"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "新名称"
    assert resp.json()["location"] == "深圳"


def test_toggle_job_active(client, auth_headers):
    created = client.post(
        "/api/jobs",
        json={"code": "JOB-300", "name": "停用测试", "location": "成都"},
        headers=auth_headers,
    ).json()
    resp = client.put(
        f"/api/jobs/{created['id']}", json={"is_active": False}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    resp = client.put(
        f"/api/jobs/{created['id']}", json={"is_active": True}, headers=auth_headers
    )
    assert resp.json()["is_active"] is True


def test_update_nonexistent_job_returns_404(client, auth_headers):
    resp = client.put("/api/jobs/999999", json={"name": "x"}, headers=auth_headers)
    assert resp.status_code == 404
