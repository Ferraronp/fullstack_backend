"""
Интеграционные тесты эндпоинта /analysis/ai.
analyze_operations мокируется целиком — реальных вызовов Groq нет.
Юнит-тесты самого сервиса — в test_services.py.
"""
import pytest
from unittest.mock import patch
from datetime import date
import services.groq_service as gs
from tests.conftest import register_and_login

ANALYZE_PATH = "routers.analysis.analyze_operations"


def _ok(text="Финансовый анализ готов"):
    """Патч: analyze_operations возвращает готовый текст."""
    async def _impl(ops):
        return text
    return patch(ANALYZE_PATH, side_effect=_impl)


class TestAnalysisEndpoint:
    def test_requires_auth(self, client):
        response = client.get("/analysis/ai")
        assert response.status_code == 401

    def test_returns_analysis_on_success(self, client):
        tokens = register_and_login(client, "analysis_user1")
        with _ok("Анализ: всё хорошо"):
            response = client.get(
                "/analysis/ai",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["analysis"] == "Анализ: всё хорошо"
        assert "operations_count" in data

    def test_operations_count_reflects_actual_data(self, client):
        tokens = register_and_login(client, "analysis_user2")
        cat = client.post(
            "/categories/", json={"name": "Food"},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        ).json()
        for i in range(2):
            client.post(
                "/operations/",
                json={"date": str(date.today()), "amount": 100.0 * (i + 1), "category_id": cat["id"]},
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        with _ok():
            response = client.get(
                "/analysis/ai",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        assert response.status_code == 200
        assert response.json()["operations_count"] == 2

    def test_zero_operations_still_works(self, client):
        tokens = register_and_login(client, "analysis_user3")
        with _ok("Операций нет"):
            response = client.get(
                "/analysis/ai",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        assert response.status_code == 200
        assert response.json()["operations_count"] == 0

    def test_limit_query_param_accepted(self, client):
        tokens = register_and_login(client, "analysis_user4")
        with _ok():
            response = client.get(
                "/analysis/ai?limit=5",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        assert response.status_code == 200

    def test_limit_below_min_returns_422(self, client):
        tokens = register_and_login(client, "analysis_user5")
        response = client.get(
            "/analysis/ai?limit=0",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert response.status_code == 422

    def test_limit_above_max_returns_422(self, client):
        tokens = register_and_login(client, "analysis_user6")
        response = client.get(
            "/analysis/ai?limit=101",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert response.status_code == 422

    def test_groq_runtime_error_returns_503(self, client):
        tokens = register_and_login(client, "analysis_user7")

        async def _fail(ops):
            raise RuntimeError("Groq недоступен")

        with patch(ANALYZE_PATH, side_effect=_fail):
            response = client.get(
                "/analysis/ai",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        assert response.status_code == 503

    def test_groq_value_error_returns_503(self, client):
        tokens = register_and_login(client, "analysis_user8")

        async def _fail(ops):
            raise ValueError("GROQ_API_KEY не задан")

        with patch(ANALYZE_PATH, side_effect=_fail):
            response = client.get(
                "/analysis/ai",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        assert response.status_code == 503
