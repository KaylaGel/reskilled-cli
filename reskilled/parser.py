import urllib.request
import urllib.error
from html.parser import HTMLParser
from pathlib import Path


class _StripHTML(HTMLParser):
    _SKIP = {"script", "style", "nav", "header", "footer", "meta", "link", "noscript"}

    def __init__(self):
        super().__init__()
        self._parts: list[str] = []
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._depth += 1

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._depth:
            self._depth -= 1

    def handle_data(self, data):
        if not self._depth:
            text = data.strip()
            if text:
                self._parts.append(text)

    @property
    def text(self) -> str:
        return "\n".join(self._parts)


def fetch_job_posting(url: str) -> str:
    """Fetch a job posting URL and return its text content.

    Returns an empty string if the page appears to be JS-rendered.
    """
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    parser = _StripHTML()
    parser.feed(html)
    text = parser.text
    return text if len(text) > 300 else ""  # short = JS-rendered, signal caller


def extract_pdf(path: str) -> str:
    """Extract plain text from a PDF file."""
    import pypdf

    pdf_path = Path(path).expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    reader = pypdf.PdfReader(str(pdf_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()
