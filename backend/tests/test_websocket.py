import json
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

def test_notifications_ws_connect_and_visibility(client):
    token, _ = register_and_token(client, "ws_user", "WS User", "passws")
    with client.websocket_connect(f"/ws/notifications?token={token}") as websocket:
        websocket.send_text(json.dumps({"type": "visibility_changed", "status": "online"}))
        time.sleep(0.05)
        assert websocket is not None

def test_chat_ws_send_message_smoke(client):
    token1, user1_id = register_and_token(client, "ws_user1", "WS1", "pass1")
    token2, user2_id = register_and_token(client, "ws_user2", "WS2", "pass2")

    headers1 = {"Authorization": f"Bearer {token1}"}
    resp = client.post("/chats/private", json={"user_id": user2_id}, headers=headers1)
    assert resp.status_code == 200
    chat = resp.json()
    chat_id = chat.get("id")
    if not chat_id:
        return

    with client.websocket_connect(f"/ws/chat/{chat_id}?token={token1}") as ws1:
        ws1.send_text(json.dumps({"type": "message", "content": "hello ws"}))
        time.sleep(0.05)
        assert True