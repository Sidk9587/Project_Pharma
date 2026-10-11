"""Small standard-library HTML parser for page text, titles and links."""

from html.parser import HTMLParser
from urllib.parse import urljoin, urldefrag


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._in_title = False
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.links: list[str] = []
        self.canonical: str | None = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"script", "style", "noscript", "svg", "template"}:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonical = attrs.get("href")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in {"script", "style", "noscript", "svg", "template"} and self._skip_depth:
            self._skip_depth -= 1
        if tag in {"p", "div", "section", "article", "li", "h1", "h2", "h3", "br", "tr"}:
            self.text_parts.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title_parts.append(data)
        if not self._skip_depth:
            normalized = " ".join(data.split())
            if normalized:
                self.text_parts.append(normalized)


def parse_html_page(html: str, page_url: str) -> dict:
    parser = PageParser()
    parser.feed(html)
    parser.close()
    title = " ".join(" ".join(parser.title_parts).split()) or page_url
    text = " ".join(" ".join(parser.text_parts).split())
    links = []
    for href in parser.links:
        absolute, _ = urldefrag(urljoin(page_url, href.strip()))
        if absolute not in links:
            links.append(absolute)
    canonical = None
    if parser.canonical:
        canonical = urldefrag(urljoin(page_url, parser.canonical.strip()))[0]
    return {"title": title, "text": text, "links": links, "canonical_url": canonical}
