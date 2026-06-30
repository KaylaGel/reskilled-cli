from rich.console import Console
import questionary
from reskilled import llm

console = Console()

_STYLE = questionary.Style([
    ("selected",    "fg:cyan bold"),
    ("pointer",     "fg:cyan bold"),
    ("highlighted", "fg:cyan"),
    ("answer",      "fg:cyan bold"),
    ("question",    "bold"),
    ("disabled",    "fg:gray italic"),
])


def _build_choices(choices: list) -> list:
    q_choices: list = []
    for c in choices:
        if c is None:
            q_choices.append(questionary.Separator())
        elif isinstance(c, str):
            q_choices.append(c)
        elif len(c) == 2 and c[1] is None:
            q_choices.append(questionary.Separator(c[0]))
        elif len(c) == 2:
            q_choices.append(questionary.Choice(c[0], value=c[1]))
        else:
            disabled = c[2] if c[2] else False
            q_choices.append(questionary.Choice(c[0], value=c[1], disabled=disabled))
    return q_choices


def select(prompt: str, choices: list) -> str | None:
    """Arrow-key selection menu.

    Each item in `choices` may be:
      - None                          → visual separator
      - str                           → simple choice (value == label)
      - (title, value)                → labelled choice
      - (title, value, disabled_msg)  → greyed-out, unselectable (msg or None)
    """
    return questionary.select(prompt, choices=_build_choices(choices), style=_STYLE).ask()


def multiselect(prompt: str, choices: list) -> list | None:
    """Checkbox multi-select. Same choice format as select(). Returns list of selected values."""
    return questionary.checkbox(prompt, choices=_build_choices(choices), style=_STYLE).ask()


def header(breadcrumb: str, subtitle: str = "") -> None:
    console.print(f"\n[dim]{breadcrumb}[/dim]")
    if subtitle:
        console.print(f"  [dim]{subtitle}[/dim]")


def stream_response(
    prompt: str,
    system: str = "",
    label: str = "Thinking",
    max_tokens: int = 2048,
) -> str:
    """Show a spinner until the first token arrives, then stream inline."""
    gen = llm.stream(prompt, system=system, max_tokens=max_tokens)

    with console.status(f"[dim]{label}...[/dim]", spinner="dots"):
        first = next(gen, None)

    result = ""
    if first:
        console.print(first, end="")
        result += first
        for chunk in gen:
            console.print(chunk, end="")
            result += chunk
    console.print()
    return result


def thinking(label: str = "Thinking") -> "console.status":
    """Spinner for non-streaming calls (complete())."""
    return console.status(f"[dim]{label}...[/dim]", spinner="dots")
