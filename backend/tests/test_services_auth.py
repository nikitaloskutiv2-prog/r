from app.services import auth_service

def test_hash_and_verify():
    pw = "MyS3cret"
    hashed = auth_service.hash_password(pw)
    assert auth_service.verify_password(pw, hashed) is True
    assert auth_service.verify_password("wrong", hashed) is False

def test_register_user_duplicate(db_session):
    # register first user
    u = auth_service.register_user(
        db=db_session,
        login="svcuser",
        username="Svc User",
        password="pw1234"
    )
    assert u is not None

    # attempt duplicate -> should raise ValueError
    try:
        auth_service.register_user(
            db=db_session,
            login="svcuser",
            username="Svc User 2",
            password="pw5678"
        )
        assert False, "Expected ValueError for duplicate login"
    except ValueError:
        pass