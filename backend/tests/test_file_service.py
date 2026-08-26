import io
import os
import pytest
import builtins

from app.services import file_service


class FakeDB:
    def __init__(self, raise_on_commit=False):
        self.raise_on_commit = raise_on_commit
        self.added = None

    def add(self, obj):
        self.added = obj

    def commit(self):
        if self.raise_on_commit:
            raise Exception("DB commit failed")

    def refresh(self, obj):
        # emulate SQLAlchemy setting an id after refresh
        if not getattr(obj, "id", None):
            obj.id = 1

    def rollback(self):
        return None


class SimpleUpload:
    def __init__(self, content: bytes, filename: str = "file.bin", content_type: str = "application/octet-stream"):
        self.filename = filename
        self.content_type = content_type
        self.file = io.BytesIO(content)


def test_get_file_size_limit():
    # image
    assert file_service.get_file_size_limit("image/png") == file_service.MAX_IMAGE_SIZE
    # video
    assert file_service.get_file_size_limit("video/mp4") == file_service.MAX_VIDEO_SIZE
    # document
    assert file_service.get_file_size_limit("application/pdf") == file_service.MAX_DOCUMENT_SIZE
    # voice returns None
    assert file_service.get_file_size_limit("audio/ogg", is_voice=True) is None


def test_save_uploaded_file_success(tmp_path, monkeypatch):
    p = tmp_path / "storage"
    p.mkdir()
    file_path = str(p / "out.bin")

    content = b"abcd" * 1024  # small content
    upload = SimpleUpload(content)

    size = file_service.save_uploaded_file(upload, file_path, max_size=10 * 1024 * 1024)
    assert size == len(content)
    assert os.path.exists(file_path)
    # cleanup
    os.remove(file_path)


def test_save_uploaded_file_exceed_removes_partial(tmp_path):
    p = tmp_path / "storage"
    p.mkdir()
    file_path = str(p / "out.bin")

    # create content > max_size to trigger ValueError
    content = b"x" * (1024 * 20)
    upload = SimpleUpload(content)

    with pytest.raises(ValueError):
        file_service.save_uploaded_file(upload, file_path, max_size=1024 * 5)

    # file should not exist after failure
    assert not os.path.exists(file_path)


def test_save_file_video_thumbnail_and_db_commit(tmp_path, monkeypatch):
    # run inside tmp_path so storage/* is created here
    monkeypatch.chdir(tmp_path)

    # Prepare fake cv2 that returns a frame and writes thumbnail
    class FakeCapture:
        def __init__(self, path):
            self.path = path
            self._read = False

        def read(self):
            # return success and a dummy frame (bytes or any object)
            return True, b"frame-bytes"

        def release(self):
            return None

    class FakeCV2:
        @staticmethod
        def VideoCapture(path):
            return FakeCapture(path)

        @staticmethod
        def imwrite(path, frame):
            # emulate writing a file
            with open(path, "wb") as f:
                if isinstance(frame, bytes):
                    f.write(frame)
                else:
                    # write dummy data
                    f.write(b"thumb")
            return True

    monkeypatch.setattr(file_service, "cv2", FakeCV2)

    content = b"video-data"
    upload = SimpleUpload(content, filename="video.mp4", content_type="video/mp4")
    db = FakeDB()

    db_file = file_service.save_file(db, upload, user_id=5)

    assert db_file.uploader_id == 5
    assert db_file.original_name == "video.mp4"
    assert db_file.mime_type == "video/mp4"
    assert db_file.size == len(content)
    assert db_file.thumbnail_path is None or "storage/thumbnails" in db_file.thumbnail_path
    # ensure stored file exists
    assert os.path.exists(db_file.path)

    # cleanup created files
    if db_file.path and os.path.exists(db_file.path):
        os.remove(db_file.path)
    if db_file.thumbnail_path:
        thumb = db_file.thumbnail_path.replace("/", os.sep)
        if os.path.exists(thumb):
            os.remove(thumb)


def test_save_file_db_error_cleanup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # Fake cv2 that does not create thumbnail
    class FakeCV2NoThumb:
        @staticmethod
        def VideoCapture(path):
            class C:
                def read(self):
                    return False, None
                def release(self):
                    pass
            return C()

        @staticmethod
        def imwrite(path, frame):
            return False

    monkeypatch.setattr(file_service, "cv2", FakeCV2NoThumb)

    content = b"video-data"
    upload = SimpleUpload(content, filename="doc.bin", content_type="application/octet-stream")
    db = FakeDB(raise_on_commit=True)

    with pytest.raises(Exception):
        file_service.save_file(db, upload, user_id=123)

    # after exception no files should remain in storage
    storage_dir = tmp_path / "storage"
    # storage may not exist if save failed early, check gracefully
    if storage_dir.exists():
        files_remaining = list(storage_dir.rglob("*"))
        # only directories may remain, but no files
        assert all(p.is_dir() for p in files_remaining) or len(files_remaining) == 0


def test_upload_voice_validation_and_success(monkeypatch):
    # negative duration
    with pytest.raises(ValueError):
        file_service.upload_voice(None, None, chat_id=1, user_id=1, duration=-1, waveform="")

    # too long
    with pytest.raises(ValueError):
        file_service.upload_voice(None, None, chat_id=1, user_id=1, duration=file_service.MAX_VOICE_DURATION + 1, waveform="")

    # success path - mock save_file to return object with required attrs
    class DummyFile:
        def __init__(self):
            self.id = 10
            self.path = "storage/files/dummy.bin"
            self.mime_type = "audio/ogg"
            self.original_name = "voice.ogg"
            self.thumbnail_path = None
            self.size = 1234

    def fake_save_file(db, uploaded_file, user_id, is_voice=False):
        return DummyFile()

    monkeypatch.setattr(file_service, "save_file", fake_save_file)

    result = file_service.upload_voice(None, SimpleUpload(b"x" * 10, filename="voice.ogg", content_type="audio/ogg"), chat_id=2, user_id=7, duration=30, waveform="[0,1,2]")

    assert result["file_id"] == 10
    assert result["duration"] == 30
    assert result["waveform"] == "[0,1,2]"
    assert result["file"]["id"] == 10
