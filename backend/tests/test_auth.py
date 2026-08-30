from tests.conftest import login


def test_login_and_me(client):
    headers = login(client)
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["user_type"] == "ADMIN"
    assert response.json()["data"]["must_change_password"] is False


def test_bad_password_is_rejected(client):
    response = client.post("/api/v1/auth/login", json={"username": "ADMIN02", "password": "wrong"})
    assert response.status_code == 401


def test_refresh_token_rotates_and_cannot_be_reused(client):
    login_response = client.post("/api/v1/auth/login", json={"username": "ADMIN02", "password": "Qwerty@123"}).json()
    token = login_response["data"]["refresh_token"]
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": token}).status_code == 200
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": token}).status_code == 401


def test_student_cannot_access_staff_routes(client, student_headers):
    assert client.get("/api/v1/classes", headers=student_headers).status_code == 403


def test_student_password_login_is_not_allowed(client):
    response = client.post("/api/v1/auth/login", json={"username": "VCEW1001", "password": "Qwerty@123"})
    assert response.status_code == 403


def test_admin_can_login_with_email_and_short_local_password(client):
    response = client.post("/api/v1/auth/login", json={"username": "dhinadts@gmail.com", "password": "1234"})
    assert response.status_code == 200
