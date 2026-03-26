"""
Модульные тесты сервисного слоя:
- groq_service: _build_prompt, analyze_operations (с мок-HTTP)
- auth_service: create_access_token, decode_access_token
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import services.groq_service as gs


# ---------------------------------------------------------------------------
# groq_service — тесты _build_prompt
# ---------------------------------------------------------------------------

class TestBuildPrompt:
    def test_empty_operations_returns_no_ops_message(self):
        result = gs._build_prompt([])
        assert "Операций нет" in result

    def test_single_operation_contains_amount_and_comment(self):
        ops = [{"date": "2024-01-01", "amount": 500.0, "comment": "Кофе", "category": {"name": "Еда"}}]
        result = gs._build_prompt(ops)
        assert "500.0" in result
        assert "Кофе" in result
        assert "Еда" in result

    def test_positive_amount_has_plus_sign(self):
        ops = [{"date": "2024-01-01", "amount": 100.0, "comment": None, "category": None}]
        result = gs._build_prompt(ops)
        assert "+100.0" in result

    def test_negative_amount_has_no_plus_sign(self):
        ops = [{"date": "2024-01-01", "amount": -50.0, "comment": None, "category": None}]
        result = gs._build_prompt(ops)
        assert "+-50" not in result

    def test_no_category_shows_fallback(self):
        ops = [{"date": "2024-01-01", "amount": 10.0, "comment": None, "category": None}]
        result = gs._build_prompt(ops)
        assert "Без категории" in result

    def test_no_comment_shows_dash(self):
        ops = [{"date": "2024-01-01", "amount": 10.0, "comment": None, "category": {"name": "X"}}]
        result = gs._build_prompt(ops)
        assert "—" in result

    def test_multiple_operations_all_present(self):
        ops = [
            {"date": "2024-01-01", "amount": 100.0, "comment": "A", "category": {"name": "C1"}},
            {"date": "2024-01-02", "amount": 200.0, "comment": "B", "category": {"name": "C2"}},
        ]
        result = gs._build_prompt(ops)
        assert "A" in result and "B" in result
        assert result.count("\n") >= 1


# ---------------------------------------------------------------------------
# groq_service — тесты analyze_operations (мок httpx)
# ---------------------------------------------------------------------------

class TestAnalyzeOperations:
    def _ok_patch(self, text="OK"):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": text}}]}
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_cls = MagicMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        return patch.object(gs.httpx, "AsyncClient", mock_cls)

    @pytest.mark.asyncio
    async def test_raises_value_error_when_no_api_key(self, monkeypatch):
        monkeypatch.setattr(gs, "GROQ_API_KEY", "")
        with pytest.raises(ValueError, match="GROQ_API_KEY"):
            await gs.analyze_operations([])

    @pytest.mark.asyncio
    async def test_returns_text_on_success(self, monkeypatch):
        monkeypatch.setattr(gs, "GROQ_API_KEY", "fake-key")
        with self._ok_patch("Анализ готов"):
            result = await gs.analyze_operations([
                {"date": "2024-01-01", "amount": 100.0, "comment": "Test", "category": None}
            ])
        assert result == "Анализ готов"

    @pytest.mark.asyncio
    async def test_raises_runtime_error_on_timeout(self, monkeypatch):
        import httpx
        monkeypatch.setattr(gs, "GROQ_API_KEY", "fake-key")
        monkeypatch.setattr(gs, "MAX_RETRIES", 0)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_cls = MagicMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch.object(gs.httpx, "AsyncClient", mock_cls):
            with pytest.raises(RuntimeError, match="Таймаут"):
                await gs.analyze_operations([])

    @pytest.mark.asyncio
    async def test_no_retry_on_rate_limit(self, monkeypatch):
        import httpx
        monkeypatch.setattr(gs, "GROQ_API_KEY", "fake-key")
        monkeypatch.setattr(gs, "MAX_RETRIES", 2)

        call_count = 0

        async def fake_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            resp = MagicMock()
            resp.status_code = 429
            raise httpx.HTTPStatusError("rate limit", request=MagicMock(), response=resp)

        mock_client = AsyncMock()
        mock_client.post = fake_post
        mock_cls = MagicMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch.object(gs.httpx, "AsyncClient", mock_cls):
            with pytest.raises(RuntimeError, match="лимит"):
                await gs.analyze_operations([])

        assert call_count == 1  # нет ретрая при 429


# ---------------------------------------------------------------------------
# auth_service — тесты токенов
# ---------------------------------------------------------------------------

class TestAuthService:
    def _make_user(self, user_id=1, role="user"):
        user = MagicMock()
        user.id = user_id
        user.role = role
        return user

    def test_create_access_token_returns_string(self):
        from services.auth_service import create_access_token
        token = create_access_token(self._make_user())
        assert isinstance(token, str) and len(token) > 0

    def test_decode_access_token_returns_correct_payload(self):
        from services.auth_service import create_access_token, decode_access_token
        user = self._make_user(user_id=42, role="admin")
        token = create_access_token(user)
        payload = decode_access_token(token)
        assert payload["user_id"] == 42
        assert payload["role"] == "admin"

    def test_decode_invalid_token_raises_401(self):
        from fastapi import HTTPException
        from services.auth_service import decode_access_token
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("totally.invalid.token")
        assert exc_info.value.status_code == 401

    def test_decode_expired_token_raises_401(self):
        from fastapi import HTTPException
        from services.auth_service import decode_access_token
        from jose import jwt
        import os

        secret = os.getenv("SECRET_KEY", "test-secret")
        expired_payload = {
            "user_id": 1,
            "role": "user",
            "exp": datetime.utcnow() - timedelta(minutes=1),
        }
        expired_token = jwt.encode(expired_payload, secret, algorithm="HS256")
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(expired_token)
        assert exc_info.value.status_code == 401
