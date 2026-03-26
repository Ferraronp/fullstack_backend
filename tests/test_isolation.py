"""
Тесты изоляции данных между пользователями и расширенная фильтрация операций.
"""
from datetime import date, timedelta
from tests.conftest import register_and_login


# ---------------------------------------------------------------------------
# Хелперы
# ---------------------------------------------------------------------------

def _create_category(client, tokens, name="Cat"):
    r = client.post(
        "/categories/", json={"name": name},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    return r.json()["id"]


def _create_operation(client, tokens, cat_id, amount=100.0, days_ago=0, comment=None):
    d = str(date.today() - timedelta(days=days_ago))
    body = {"date": d, "amount": amount, "category_id": cat_id}
    if comment:
        body["comment"] = comment
    return client.post(
        "/operations/", json=body,
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    ).json()


# ---------------------------------------------------------------------------
# Изоляция: категории
# ---------------------------------------------------------------------------

class TestCategoryIsolation:
    def test_user_sees_only_own_categories(self, client):
        ta = register_and_login(client, "iso_cat_a")
        tb = register_and_login(client, "iso_cat_b")
        _create_category(client, ta, "A_cat")
        _create_category(client, tb, "B_cat")

        r = client.get("/categories/", headers={"Authorization": f"Bearer {ta['access_token']}"})
        names = [c["name"] for c in r.json()]
        assert "A_cat" in names
        assert "B_cat" not in names

    def test_user_cannot_get_other_users_category(self, client):
        ta = register_and_login(client, "iso_cat_c")
        tb = register_and_login(client, "iso_cat_d")
        cat_id = _create_category(client, ta, "A_private")

        r = client.get(
            f"/categories/{cat_id}",
            headers={"Authorization": f"Bearer {tb['access_token']}"},
        )
        assert r.status_code == 404

    def test_user_cannot_update_other_users_category(self, client):
        ta = register_and_login(client, "iso_cat_e")
        tb = register_and_login(client, "iso_cat_f")
        cat_id = _create_category(client, ta, "A_cat")

        r = client.put(
            f"/categories/{cat_id}",
            json={"name": "Hacked"},
            headers={"Authorization": f"Bearer {tb['access_token']}"},
        )
        assert r.status_code in (403, 404)

    def test_user_cannot_delete_other_users_category(self, client):
        ta = register_and_login(client, "iso_cat_g")
        tb = register_and_login(client, "iso_cat_h")
        cat_id = _create_category(client, ta, "A_cat")

        r = client.delete(
            f"/categories/{cat_id}",
            headers={"Authorization": f"Bearer {tb['access_token']}"},
        )
        assert r.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Изоляция: операции
# ---------------------------------------------------------------------------

class TestOperationIsolation:
    def test_user_sees_only_own_operations(self, client):
        ta = register_and_login(client, "iso_op_a")
        tb = register_and_login(client, "iso_op_b")
        cat_a = _create_category(client, ta, "CatA")
        cat_b = _create_category(client, tb, "CatB")
        _create_operation(client, ta, cat_a, amount=111.0)
        _create_operation(client, tb, cat_b, amount=222.0)

        r = client.get("/operations/", headers={"Authorization": f"Bearer {ta['access_token']}"})
        amounts = [op["amount"] for op in r.json()["items"]]
        assert 111.0 in amounts
        assert 222.0 not in amounts

    def test_user_cannot_get_other_users_operation(self, client):
        ta = register_and_login(client, "iso_op_c")
        tb = register_and_login(client, "iso_op_d")
        cat = _create_category(client, ta, "C")
        op = _create_operation(client, ta, cat, amount=50.0)

        r = client.get(
            f"/operations/{op['id']}",
            headers={"Authorization": f"Bearer {tb['access_token']}"},
        )
        assert r.status_code == 404

    def test_user_cannot_update_other_users_operation(self, client):
        ta = register_and_login(client, "iso_op_e")
        tb = register_and_login(client, "iso_op_f")
        cat = _create_category(client, ta, "C")
        op = _create_operation(client, ta, cat)

        r = client.put(
            f"/operations/{op['id']}",
            json={"date": str(date.today()), "amount": 999.0, "category_id": cat},
            headers={"Authorization": f"Bearer {tb['access_token']}"},
        )
        assert r.status_code == 404

    def test_user_cannot_delete_other_users_operation(self, client):
        ta = register_and_login(client, "iso_op_g")
        tb = register_and_login(client, "iso_op_h")
        cat = _create_category(client, ta, "C")
        op = _create_operation(client, ta, cat)

        r = client.delete(
            f"/operations/{op['id']}",
            headers={"Authorization": f"Bearer {tb['access_token']}"},
        )
        assert r.status_code == 404

    def test_balance_is_per_user(self, client):
        ta = register_and_login(client, "iso_bal_a")
        tb = register_and_login(client, "iso_bal_b")
        cat_a = _create_category(client, ta, "CatA")
        cat_b = _create_category(client, tb, "CatB")
        _create_operation(client, ta, cat_a, amount=300.0)
        _create_operation(client, tb, cat_b, amount=500.0)

        r = client.get("/operations/balance/total", headers={"Authorization": f"Bearer {ta['access_token']}"})
        assert r.json()["balance"] == 300.0


# ---------------------------------------------------------------------------
# Фильтрация, сортировка, пагинация операций
# ---------------------------------------------------------------------------

class TestOperationFilters:
    def setup_method(self):
        """Данные инициализируются в каждом тесте через client fixture."""

    def _setup_data(self, client):
        tokens = register_and_login(client, f"filter_user_{id(self)}")
        cat = _create_category(client, tokens, "FilterCat")
        today = date.today()
        _create_operation(client, tokens, cat, amount=100.0, days_ago=0, comment="alpha")
        _create_operation(client, tokens, cat, amount=200.0, days_ago=1, comment="beta")
        _create_operation(client, tokens, cat, amount=50.0, days_ago=2, comment="gamma")
        return tokens, cat

    def test_filter_by_start_date(self, client):
        tokens = register_and_login(client, "flt_date1")
        cat = _create_category(client, tokens, "C")
        _create_operation(client, tokens, cat, amount=100.0, days_ago=0)
        _create_operation(client, tokens, cat, amount=200.0, days_ago=5)

        today = str(date.today())
        r = client.get(
            f"/operations/?start_date={today}&end_date={today}",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert r.json()["total"] == 1
        assert r.json()["items"][0]["amount"] == 100.0

    def test_filter_by_min_amount(self, client):
        tokens = register_and_login(client, "flt_amt1")
        cat = _create_category(client, tokens, "C")
        _create_operation(client, tokens, cat, amount=10.0)
        _create_operation(client, tokens, cat, amount=500.0)

        r = client.get(
            "/operations/?min_amount=100",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert all(op["amount"] >= 100 for op in r.json()["items"])

    def test_filter_by_max_amount(self, client):
        tokens = register_and_login(client, "flt_amt2")
        cat = _create_category(client, tokens, "C")
        _create_operation(client, tokens, cat, amount=10.0)
        _create_operation(client, tokens, cat, amount=500.0)

        r = client.get(
            "/operations/?max_amount=100",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert all(op["amount"] <= 100 for op in r.json()["items"])

    def test_filter_min_greater_than_max_returns_422(self, client):
        tokens = register_and_login(client, "flt_amt3")
        r = client.get(
            "/operations/?min_amount=500&max_amount=100",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert r.status_code == 422

    def test_filter_by_comment(self, client):
        tokens = register_and_login(client, "flt_cmt1")
        cat = _create_category(client, tokens, "C")
        _create_operation(client, tokens, cat, amount=10.0, comment="unique_xyz")
        _create_operation(client, tokens, cat, amount=20.0, comment="other")

        r = client.get(
            "/operations/?comment=unique_xyz",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert r.json()["total"] == 1

    def test_filter_by_category_id(self, client):
        tokens = register_and_login(client, "flt_cat1")
        cat1 = _create_category(client, tokens, "Cat1")
        cat2 = _create_category(client, tokens, "Cat2")
        _create_operation(client, tokens, cat1, amount=100.0)
        _create_operation(client, tokens, cat2, amount=200.0)

        r = client.get(
            f"/operations/?category_id={cat1}",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert r.json()["total"] == 1
        assert r.json()["items"][0]["amount"] == 100.0

    def test_sort_by_amount_asc(self, client):
        tokens = register_and_login(client, "flt_sort1")
        cat = _create_category(client, tokens, "C")
        _create_operation(client, tokens, cat, amount=300.0)
        _create_operation(client, tokens, cat, amount=100.0)
        _create_operation(client, tokens, cat, amount=200.0)

        r = client.get(
            "/operations/?sort_by=amount&sort_order=asc",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        amounts = [op["amount"] for op in r.json()["items"]]
        assert amounts == sorted(amounts)

    def test_sort_by_amount_desc(self, client):
        tokens = register_and_login(client, "flt_sort2")
        cat = _create_category(client, tokens, "C")
        _create_operation(client, tokens, cat, amount=300.0)
        _create_operation(client, tokens, cat, amount=100.0)
        _create_operation(client, tokens, cat, amount=200.0)

        r = client.get(
            "/operations/?sort_by=amount&sort_order=desc",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        amounts = [op["amount"] for op in r.json()["items"]]
        assert amounts == sorted(amounts, reverse=True)

    def test_pagination_page_size(self, client):
        tokens = register_and_login(client, "flt_pag1")
        cat = _create_category(client, tokens, "C")
        for i in range(5):
            _create_operation(client, tokens, cat, amount=float(i * 10 + 10))

        r = client.get(
            "/operations/?page=1&page_size=2",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        data = r.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5

    def test_pagination_second_page(self, client):
        tokens = register_and_login(client, "flt_pag2")
        cat = _create_category(client, tokens, "C")
        for i in range(5):
            _create_operation(client, tokens, cat, amount=float(i * 10 + 10))

        r1 = client.get(
            "/operations/?page=1&page_size=3&sort_by=amount&sort_order=asc",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        r2 = client.get(
            "/operations/?page=2&page_size=3&sort_by=amount&sort_order=asc",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        ids_p1 = {op["id"] for op in r1.json()["items"]}
        ids_p2 = {op["id"] for op in r2.json()["items"]}
        assert ids_p1.isdisjoint(ids_p2)

    def test_page_size_max_100(self, client):
        tokens = register_and_login(client, "flt_pag3")
        r = client.get(
            "/operations/?page_size=101",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert r.status_code == 422

    def test_page_min_1(self, client):
        tokens = register_and_login(client, "flt_pag4")
        r = client.get(
            "/operations/?page=0",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert r.status_code == 422
