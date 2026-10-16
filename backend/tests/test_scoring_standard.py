def _create_job(client, headers, code="JOB-SS-1"):
    return client.post(
        "/api/jobs",
        json={"code": code, "name": "评分测试", "location": "厦门"},
        headers=headers,
    ).json()


A_TABLE_VALID = [
    {"category": "学历", "subcategory": "学历", "category_score": 2, "subcategory_score": 2},
    {
        "category": "工作经验",
        "subcategory": "工作经验",
        "category_score": 3,
        "subcategory_score": 3,
    },
    {
        "category": "项目经验",
        "subcategory": "项目经验",
        "category_score": 3,
        "subcategory_score": 3,
    },
    {
        "category": "个人技能",
        "subcategory": "个人技能",
        "category_score": 2,
        "subcategory_score": 2,
    },
]

B_TABLE_VALID = [
    {
        "category": "学历",
        "subcategory": "学历",
        "level1_indicator": "最高学历",
        "level2_indicator": "硕士及以上",
        "weight": 10,
    },
    {
        "category": "学历",
        "subcategory": "学历",
        "level1_indicator": "最高学历",
        "level2_indicator": "本科",
        "weight": 8,
    },
]


def test_get_scoring_standard_empty(client, auth_headers):
    job = _create_job(client, auth_headers)
    resp = client.get(f"/api/jobs/{job['id']}/scoring-standard", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"a": [], "b": []}


def test_put_a_table_success(client, auth_headers):
    job = _create_job(client, auth_headers)
    resp = client.put(
        f"/api/jobs/{job['id']}/scoring-standard/a", json=A_TABLE_VALID, headers=auth_headers
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 4

    data = client.get(f"/api/jobs/{job['id']}/scoring-standard", headers=auth_headers).json()
    assert len(data["a"]) == 4


def test_put_a_table_invalid_total_returns_400(client, auth_headers):
    job = _create_job(client, auth_headers)
    rows = [
        {"category": "学历", "subcategory": "学历", "category_score": 2, "subcategory_score": 2},
    ]
    resp = client.put(f"/api/jobs/{job['id']}/scoring-standard/a", json=rows, headers=auth_headers)
    assert resp.status_code == 400


def test_put_a_table_subcategory_sum_mismatch_returns_400(client, auth_headers):
    job = _create_job(client, auth_headers)
    rows = [
        {"category": "A", "subcategory": "A1", "category_score": 5, "subcategory_score": 3},
        {"category": "A", "subcategory": "A2", "category_score": 5, "subcategory_score": 1},
        {"category": "B", "subcategory": "B1", "category_score": 5, "subcategory_score": 5},
    ]
    resp = client.put(f"/api/jobs/{job['id']}/scoring-standard/a", json=rows, headers=auth_headers)
    assert resp.status_code == 400


def test_put_a_table_inconsistent_category_score_returns_400(client, auth_headers):
    job = _create_job(client, auth_headers)
    rows = [
        {"category": "A", "subcategory": "A1", "category_score": 5, "subcategory_score": 5},
        {"category": "A", "subcategory": "A2", "category_score": 7, "subcategory_score": 0},
        {"category": "B", "subcategory": "B1", "category_score": 5, "subcategory_score": 5},
    ]
    resp = client.put(f"/api/jobs/{job['id']}/scoring-standard/a", json=rows, headers=auth_headers)
    assert resp.status_code == 400


def test_put_a_table_duplicate_subcategory_returns_400(client, auth_headers):
    job = _create_job(client, auth_headers)
    rows = [
        {"category": "A", "subcategory": "X", "category_score": 5, "subcategory_score": 5},
        {"category": "B", "subcategory": "X", "category_score": 5, "subcategory_score": 5},
    ]
    resp = client.put(f"/api/jobs/{job['id']}/scoring-standard/a", json=rows, headers=auth_headers)
    assert resp.status_code == 400


def test_put_a_table_out_of_range_score_returns_400(client, auth_headers):
    job = _create_job(client, auth_headers)
    rows = [
        {"category": "A", "subcategory": "A1", "category_score": 12, "subcategory_score": 12},
        {"category": "B", "subcategory": "B1", "category_score": -2, "subcategory_score": -2},
    ]
    resp = client.put(f"/api/jobs/{job['id']}/scoring-standard/a", json=rows, headers=auth_headers)
    assert resp.status_code == 400


def test_put_b_table_success(client, auth_headers):
    job = _create_job(client, auth_headers)
    resp = client.put(
        f"/api/jobs/{job['id']}/scoring-standard/b", json=B_TABLE_VALID, headers=auth_headers
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_put_b_table_invalid_weight_returns_400(client, auth_headers):
    job = _create_job(client, auth_headers)
    rows = [
        {
            "category": "学历",
            "subcategory": "学历",
            "level1_indicator": "最高学历",
            "level2_indicator": "硕士",
            "weight": 1,
        },
    ]
    resp = client.put(f"/api/jobs/{job['id']}/scoring-standard/b", json=rows, headers=auth_headers)
    assert resp.status_code == 400


def test_scoring_standard_requires_auth(client):
    assert client.get("/api/jobs/1/scoring-standard").status_code == 401


def test_seed_standard_present(client, auth_headers):
    jobs = client.get("/api/jobs", headers=auth_headers).json()
    demo = next(j for j in jobs if j["code"] == "DEMO-JOB-001")
    data = client.get(f"/api/jobs/{demo['id']}/scoring-standard", headers=auth_headers).json()
    assert len(data["a"]) > 0
    assert len(data["b"]) > 0
