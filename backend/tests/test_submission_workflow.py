def test_admin_overview_is_college_wide(client, admin_headers):
    response = client.get("/api/v1/submissions/admin-overview", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["academic_year"] == "2026-2027"
    assert data["students"] == 10
    assert data["professors"] == 1


def test_professor_cannot_open_admin_overview(client, professor_headers):
    response = client.get("/api/v1/submissions/admin-overview", headers=professor_headers)
    assert response.status_code == 403
