"""
Интеграционные тесты файловых эндпоинтов (S3 мокируется).
POST   /operations/{id}/files
GET    /operations/{id}/files/{fid}/url
DELETE /operations/{id}/files/{fid}
"""
import io
import pytest
from unittest.mock import patch, MagicMock
from datetime import date
from tests.conftest import register_and_login


# ---------------------------------------------------------------------------
# Хелперы
# ---------------------------------------------------------------------------

def _make_operation(client, tokens, amount=100.0):
    cat = client.post(
        "/categories/", json={"name": "TestCat"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    ).json()
    op = client.post(
        "/operations/",
        json={"date": str(date.today()), "amount": amount, "category_id": cat["id"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    ).json()
    return op["id"]


def _s3_patches(s3_key="fake-key-123.pdf", presigned_url="http://minio/fake-key-123.pdf"):
    """Патчи для upload_file, get_presigned_url, delete_file."""
    return [
        patch("services.s3_service.upload_file", return_value=s3_key),
        patch("services.s3_service.get_presigned_url", return_value=presigned_url),
        patch("services.s3_service.delete_file", return_value=None),
    ]


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

class TestFileUpload:
    def test_upload_pdf_success(self, client):
        tokens = register_and_login(client, "fup1")
        op_id = _make_operation(client, tokens)

        with patch("services.s3_service.upload_file", return_value="uuid.pdf"):
            response = client.post(
                f"/operations/{op_id}/files",
                files={"file": ("receipt.pdf", b"%PDF-content", "application/pdf")},
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "receipt.pdf"
        assert "id" in data

    def test_upload_image_success(self, client):
        tokens = register_and_login(client, "fup2")
        op_id = _make_operation(client, tokens)

        with patch("services.s3_service.upload_file", return_value="uuid.jpg"):
            response = client.post(
                f"/operations/{op_id}/files",
                files={"file": ("photo.jpg", b"\xff\xd8\xff", "image/jpeg")},
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        assert response.status_code == 200

    def test_upload_disallowed_type_returns_400(self, client):
        tokens = register_and_login(client, "fup3")
        op_id = _make_operation(client, tokens)

        response = client.post(
            f"/operations/{op_id}/files",
            files={"file": ("script.exe", b"MZ", "application/octet-stream")},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"].lower()

    def test_upload_oversized_file_returns_400(self, client):
        import services.s3_service as s3
        tokens = register_and_login(client, "fup4")
        op_id = _make_operation(client, tokens)

        oversized = b"x" * (s3.MAX_FILE_SIZE_BYTES + 1)
        with patch("services.s3_service.upload_file", return_value="k"):
            response = client.post(
                f"/operations/{op_id}/files",
                files={"file": ("big.pdf", oversized, "application/pdf")},
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        assert response.status_code == 400
        assert "large" in response.json()["detail"].lower()

    def test_upload_to_nonexistent_operation_returns_404(self, client):
        tokens = register_and_login(client, "fup5")

        with patch("services.s3_service.upload_file", return_value="k"):
            response = client.post(
                "/operations/99999/files",
                files={"file": ("f.pdf", b"%PDF", "application/pdf")},
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        assert response.status_code == 404

    def test_upload_requires_auth(self, client):
        response = client.post(
            "/operations/1/files",
            files={"file": ("f.pdf", b"%PDF", "application/pdf")},
        )
        assert response.status_code == 401

    def test_upload_to_other_users_operation_returns_404(self, client):
        """Юзер B не может загрузить файл к операции юзера A."""
        tokens_a = register_and_login(client, "fup_a")
        tokens_b = register_and_login(client, "fup_b")
        op_id = _make_operation(client, tokens_a)

        with patch("services.s3_service.upload_file", return_value="k"):
            response = client.post(
                f"/operations/{op_id}/files",
                files={"file": ("f.pdf", b"%PDF", "application/pdf")},
                headers={"Authorization": f"Bearer {tokens_b['access_token']}"},
            )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Get presigned URL
# ---------------------------------------------------------------------------

class TestFileUrl:
    def _upload_file(self, client, tokens, op_id):
        with patch("services.s3_service.upload_file", return_value="uuid.pdf"):
            r = client.post(
                f"/operations/{op_id}/files",
                files={"file": ("r.pdf", b"%PDF", "application/pdf")},
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        return r.json()["id"]

    def test_get_url_returns_presigned_url(self, client):
        tokens = register_and_login(client, "furl1")
        op_id = _make_operation(client, tokens)
        fid = self._upload_file(client, tokens, op_id)

        with patch("services.s3_service.get_presigned_url", return_value="http://minio/signed"):
            response = client.get(
                f"/operations/{op_id}/files/{fid}/url",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "http://minio/signed"
        assert "filename" in data
        assert "expires_in" in data

    def test_get_url_for_nonexistent_file_returns_404(self, client):
        tokens = register_and_login(client, "furl2")
        op_id = _make_operation(client, tokens)

        response = client.get(
            f"/operations/{op_id}/files/99999/url",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert response.status_code == 404

    def test_get_url_for_other_users_operation_returns_404(self, client):
        tokens_a = register_and_login(client, "furl_a")
        tokens_b = register_and_login(client, "furl_b")
        op_id = _make_operation(client, tokens_a)
        fid = self._upload_file(client, tokens_a, op_id)

        with patch("services.s3_service.get_presigned_url", return_value="http://x"):
            response = client.get(
                f"/operations/{op_id}/files/{fid}/url",
                headers={"Authorization": f"Bearer {tokens_b['access_token']}"},
            )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete file
# ---------------------------------------------------------------------------

class TestFileDelete:
    def _upload_file(self, client, tokens, op_id):
        with patch("services.s3_service.upload_file", return_value="uuid.pdf"):
            r = client.post(
                f"/operations/{op_id}/files",
                files={"file": ("r.pdf", b"%PDF", "application/pdf")},
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        return r.json()["id"]

    def test_delete_file_success(self, client):
        tokens = register_and_login(client, "fdel1")
        op_id = _make_operation(client, tokens)
        fid = self._upload_file(client, tokens, op_id)

        with patch("services.s3_service.delete_file"):
            response = client.delete(
                f"/operations/{op_id}/files/{fid}",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        assert response.status_code == 200
        assert "deleted" in response.json().get("detail", "").lower()

    def test_delete_nonexistent_file_returns_404(self, client):
        tokens = register_and_login(client, "fdel2")
        op_id = _make_operation(client, tokens)

        with patch("services.s3_service.delete_file"):
            response = client.delete(
                f"/operations/{op_id}/files/99999",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        assert response.status_code == 404

    def test_delete_calls_s3_delete(self, client):
        """Удаление файла должно вызвать s3_service.delete_file."""
        tokens = register_and_login(client, "fdel3")
        op_id = _make_operation(client, tokens)
        fid = self._upload_file(client, tokens, op_id)

        with patch("services.s3_service.delete_file") as mock_del:
            client.delete(
                f"/operations/{op_id}/files/{fid}",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        mock_del.assert_called_once()

    def test_delete_operation_also_deletes_s3_files(self, client):
        """При удалении операции все её файлы должны быть удалены из S3."""
        tokens = register_and_login(client, "fdel4")
        op_id = _make_operation(client, tokens)
        self._upload_file(client, tokens, op_id)

        with patch("services.s3_service.delete_file") as mock_del:
            client.delete(
                f"/operations/{op_id}",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        mock_del.assert_called_once()
