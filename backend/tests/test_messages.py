import time

def register_and_token(client, login, username, password="pass1234"):
    r = client.post("/auth/register", json={
        "login": login,
        "username": username,
        "password": password
    })
    assert r.status_code in (200, 201)
    data = r.json()
    return data["access_token"], data["user_id"]

def test_send_message_and_mark_read(client):
    token1, user1_id = register_and_token(client, "msg_user1", "Msg One", "pass1")
    token2, user2_id = register_and_token(client, "msg_user2", "Msg Two", "pass2")

    headers1 = {"Authorization": f"Bearer {token1}"}
    resp = client.post("/chats/private", json={"user_id": user2_id}, headers=headers1)
    assert resp.status_code == 200
    chat = resp.json()
    chat_id = chat.get("id")
    assert chat_id is not None

    payload = {"chat_id": chat_id, "content": "Hello from test"}
    r = client.post("/messages/", json=payload, headers=headers1)
    assert r.status_code in (200, 201)
    msg = r.json()
    assert msg.get("content") == "Hello from test"

    headers2 = {"Authorization": f"Bearer {token2}"}
    mid = msg.get("id")
    r2 = client.put(f"/messages/{mid}/read", headers=headers2)
    assert r2.status_code == 200
    j = r2.json()
    assert j.get("is_read") is True or j.get("id") == mid

def test_unread_counts(client):
    token, _ = register_and_token(client, "unread_user", "Unread", "passun")
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/messages/unread/counts", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)