def test_register_login_and_me(client):
    # register
    resp = client.post("/auth/register", json={
        "login": "testuser",
        "username": "Test User",
        "password": "pass1234"
    })
    # API sometimes returns 200 or 201 in this project; accept both
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert "access_token" in data
    assert "user_id" in data

    # login
    resp2 = client.post("/auth/login", json={
        "login": "testuser",
        "password": "pass1234"
    })
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["username"] == "Test User"

    # protected endpoint
    token = data2["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["username"] == "Test User"

def test_register_duplicate(client):
    # create base user
    resp = client.post("/auth/register", json={
        "login": "dupuser",
        "username": "Dup User",
        "password": "dup-pass123"
    })
    assert resp.status_code in (200, 201)

    # attempt to register again -> expect 400
    resp2 = client.post("/auth/register", json={
        "login": "dupuser",
        "username": "Dup User 2",
        "password": "dup-pass123"
    })
    assert resp2.status_code == 400