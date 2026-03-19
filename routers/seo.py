from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

router = APIRouter(tags=["SEO"])

BASE_URL = "http://localhost:5173"


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    return """User-agent: *
Allow: /
Allow: /login
Allow: /register

Disallow: /operations
Disallow: /add-operation
Disallow: /add-category
Disallow: /settings
Disallow: /report

Sitemap: http://localhost:8000/sitemap.xml
"""


@router.get("/sitemap.xml")
def sitemap_xml():
    urls = [
        {"loc": f"{BASE_URL}/", "priority": "0.5"},
        {"loc": f"{BASE_URL}/login", "priority": "1.0"},
        {"loc": f"{BASE_URL}/register", "priority": "0.8"},
    ]
    items = "\n".join(
        f"""  <url>
    <loc>{u["loc"]}</loc>
    <changefreq>weekly</changefreq>
    <priority>{u["priority"]}</priority>
  </url>"""
        for u in urls
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{items}
</urlset>"""
    return Response(content=xml, media_type="application/xml")
