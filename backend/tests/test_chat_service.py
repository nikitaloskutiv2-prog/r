import pytest
from datetime import datetime, timedelta

from app.services import chat_service


class DummyUser:
    def __init__(self, id, username="u"):
        self.id = id
        self.username = username


class DummyChat:
    def __init__(self, id=1, members=None, is_private=True, is_favorite=False, name=None):
        self.id = id
        self.members = members or []
        self.is_private = is_private
        self.is_favorite = is_favorite
        self.name = name


class DummyMessage:
    def __init__(self, id, chat_id, created_at=None):
        self.id = id
        self.chat_id = chat_id
        self.created_at = created_at or datetime.utcnow()


class DummyDeletion:
    def __init__(self, chat_id, user_id, created_at=None):
        self.chat_id = chat_id
        self.user_id = user_id
        self.created_at = created_at or datetime.utcnow() - timedelta(days=1)


class FakeDB:
    def __init__(self):
        self.committed = False
        self.added = []
        self.deleted = []

    def query(self, model):
        # naive query emulation by returning self in chain
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return None

    def all(self):
        return []

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        obj.id = getattr(obj, 'id', 999)

    def delete(self, obj):
        self.deleted.append(obj)

    def query_returning(self, data):
        # helper not used in tests but available
        return data


def test_get_chat_name_private():
    user1 = DummyUser(1, username='alice')
    user2 = DummyUser(2, username='bob')
    chat = DummyChat(id=10, members=[user1, user2], is_private=True)

    name = chat_service.get_chat_name(chat, current_user_id=1)
    assert name == 'bob'


def test_get_chat_name_favorite():
    chat = DummyChat(is_favorite=True)
    assert chat_service.get_chat_name(chat, current_user_id=1) == 'Избранное'


def test_get_or_create_favorite_chat_create(monkeypatch):
    # simulate DB returning no chat and returning a user when queried
    class DB:
        def query(self, model):
            class Q:
                def filter(self, *a, **k):
                    return self

                def first(self):
                    return None

                def all(self):
                    return [DummyUser(42)]
            return Q()

    db = DB()

    chat = chat_service.get_or_create_favorite_chat(db, user_id=42)
    assert chat is not None
    assert chat.is_favorite is True
    assert chat.members[0].id == 42


def test_get_or_create_private_chat_user_missing(monkeypatch):
    # simulate missing user
    class DB:
        def query(self, model):
            class Q:
                def filter(self, *a, **k):
                    return self

                def first(self):
                    return None

                def all(self):
                    return []
            return Q()

    db = DB()
    res = chat_service.get_or_create_private_chat(db, 1, 2)
    assert res is None


def test_delete_chat_for_me_not_found(monkeypatch):
    class DB:
        def query(self, model):
            return self

        def filter(self, *a, **k):
            return self

        def first(self):
            return None

    db = DB()
    res = chat_service.delete_chat_for_me(db, 1, 1)
    assert res is False


def test_delete_chat_for_all_denied_conditions():
    # chat not private
    class DB:
        def query(self, model):
            class Q:
                def filter(self, *a, **k):
                    return self

                def first(self):
                    return DummyChat(id=1, members=[DummyUser(1), DummyUser(2)], is_private=False)

            return Q()

    db = DB()
    assert chat_service.delete_chat_for_all(db, 1, 1) is False

