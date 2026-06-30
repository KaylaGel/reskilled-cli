import webbrowser
import typer
from rich.console import Console
from rich.prompt import Prompt
from reskilled import llm, ui

app = typer.Typer(help="Find events and communities")
console = Console()

PLATFORMS = {
    "meetup": {
        "name": "Meetup",
        "description": "Local tech groups and recurring events",
        "url": "https://www.meetup.com/find/?keywords={q}&source=EVENTS",
    },
    "luma": {
        "name": "Luma",
        "description": "Curated tech events and communities",
        "url": "https://lu.ma/search?q={q}",
    },
    "eventbrite": {
        "name": "Eventbrite",
        "description": "Workshops, conferences, and professional events",
        "url": "https://www.eventbrite.com/d/online/{q}/",
    },
}


def menu() -> None:
    while True:
        ui.header("reskilled › Network", "Find communities and events to accelerate your learning.")

        choices = [
            (f"{v['name']}  [dim]{v['description']}[/dim]", k)
            for k, v in PLATFORMS.items()
        ] + [
            None,
            ("← Back", "back"),
        ]

        choice = ui.select("Platform", choices)

        if not choice or choice == "back":
            break
        _find(choice)


@app.command("find")
def find(
    platform: str = typer.Option(None, "--platform", "-p", help="meetup | luma | eventbrite"),
):
    """Find events and communities on a platform."""
    if not platform or platform not in PLATFORMS:
        menu()
        return
    _find(platform)


def _find(platform_key: str) -> None:
    p = PLATFORMS[platform_key]
    topic = Prompt.ask(f"\nWhat are you looking for on [bold]{p['name']}[/bold]")

    prompt = f"""Give 5 specific search terms to find the best {p['name']} communities or events for someone learning {topic}.
Return only the search terms, one per line, no numbering or explanation."""

    with ui.thinking("Finding search terms"):
        raw = llm.complete(prompt, max_tokens=200)
    terms = [t.strip() for t in raw.strip().splitlines() if t.strip()][:5]

    console.print()
    choice = ui.select("Open which search?", [(t, i) for i, t in enumerate(terms, 1)])

    if choice is None:
        return

    query = terms[choice - 1].replace(" ", "+")
    url = p["url"].format(q=query)

    console.print(f"\n[dim]Opening → {url}[/dim]")
    webbrowser.open(url)
