def register_and_token(client, login, username, password="pass1234"):
    r = client.post("/auth/register", json={
        "login": login,
        "username": username,
        "password": password
    })
    assert r.status_code in (200, 201)
    data = r.json()
    return data["access_token"], data["user_id"]

def test_create_private_chat_and_list(client):
    token1, user1_id = register_and_token(client, "chat_user1", "User One", "pass1")
    token2, user2_id = register_and_token(client, "chat_user2", "User Two", "pass2")

    headers = {"Authorization": f"Bearer {token1}"}
    resp = client.post("/chats/private", json={"user_id": user2_id}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("id") is not None or data.get("is_private", False) is True

    r = client.get("/chats/", headers=headers)
    assert r.status_code == 200
    chats = r.json()
    assert isinstance(chats, list)

def test_favorite_chat_creation(client):
    token, _ = register_and_token(client, "fav_user", "Fav User", "passfav")
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post("/chats/favorite", headers=headers)
    assert r.status_code == 200
    j = r.json()
    assert j.get("is_favorite") is True or j.get("name") == "Избранное"