"""
Тесты SEO-эндпоинтов: robots.txt и sitemap.xml.
Эндпоинты публичные (авторизация не требуется).
"""


def test_robots_txt_status_and_content_type(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_robots_txt_allows_public_routes(client):
    body = client.get("/robots.txt").text
    assert "Allow: /login" in body
    assert "Allow: /register" in body


def test_robots_txt_disallows_private_routes(client):
    body = client.get("/robots.txt").text
    assert "Disallow: /operations" in body
    assert "Disallow: /settings" in body
    assert "Disallow: /report" in body


def test_robots_txt_contains_sitemap_reference(client):
    body = client.get("/robots.txt").text
    assert "Sitemap:" in body
    assert "sitemap.xml" in body


def test_sitemap_xml_status_and_content_type(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert "xml" in response.headers["content-type"]


def test_sitemap_xml_is_valid_xml(client):
    import xml.etree.ElementTree as ET
    body = client.get("/sitemap.xml").text
    # не бросает исключение — значит валидный XML
    root = ET.fromstring(body)
    assert root.tag.endswith("urlset")


def test_sitemap_xml_contains_public_urls(client):
    body = client.get("/sitemap.xml").text
    assert "/login" in body
    assert "/register" in body


def test_sitemap_xml_does_not_contain_private_urls(client):
    body = client.get("/sitemap.xml").text
    assert "/operations" not in body
    assert "/settings" not in body


def test_sitemap_xml_has_priority_tags(client):
    body = client.get("/sitemap.xml").text
    assert "<priority>" in body


def test_sitemap_xml_has_changefreq_tags(client):
    body = client.get("/sitemap.xml").text
    assert "<changefreq>" in body
