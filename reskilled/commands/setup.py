from rich.console import Console
from rich.prompt import IntPrompt, Prompt, Confirm
from rich.panel import Panel
from rich import print
from reskilled import config

console = Console()

PROVIDERS = [
    {
        "name": "Anthropic",
        "models": [
            ("claude-sonnet-4-6",          "Sonnet 4.6   — fast, balanced          ✦ recommended"),
            ("claude-opus-4-7",             "Opus 4.7     — most capable"),
            ("claude-haiku-4-5-20251001",   "Haiku 4.5    — fastest, cheapest"),
        ],
        "env_var": "ANTHROPIC_API_KEY",
        "needs_key": True,
        "key_url": "https://console.anthropic.com/settings/keys",
    },
    {
        "name": "OpenAI",
        "models": [
            ("gpt-4o",      "GPT-4o      — most capable"),
            ("gpt-4o-mini", "GPT-4o mini — fast & affordable  ✦ recommended"),
        ],
        "env_var": "OPENAI_API_KEY",
        "needs_key": True,
        "key_url": "https://platform.openai.com/api-keys",
    },
    {
        "name": "Google Gemini",
        "models": [
            ("gemini/gemini-2.0-flash", "Gemini 2.0 Flash — fast & capable    ✦ recommended"),
            ("gemini/gemini-1.5-pro",   "Gemini 1.5 Pro   — strong reasoning"),
        ],
        "env_var": "GEMINI_API_KEY",
        "needs_key": True,
        "key_url": "https://aistudio.google.com/app/apikey",
    },
    {
        "name": "Groq  (free tier available)",
        "models": [
            ("groq/llama-3.3-70b-versatile", "Llama 3.3 70B  — powerful open source ✦ recommended"),
            ("groq/mixtral-8x7b-32768",       "Mixtral 8x7B   — fast"),
        ],
        "env_var": "GROQ_API_KEY",
        "needs_key": True,
        "key_url": "https://console.groq.com/keys",
    },
    {
        "name": "Ollama  (local, completely free)",
        "models": [
            ("ollama/llama3.2", "Llama 3.2   — balanced"),
            ("ollama/mistral",  "Mistral     — fast"),
            ("ollama/codellama","CodeLlama   — code-focused"),
        ],
        "env_var": None,
        "needs_key": False,
        "key_url": None,
    },
]


def run(force: bool = False) -> None:
    if config.is_configured() and not force:
        c = config.load()
        if not Confirm.ask(f"Already configured: [bold]{c['model']}[/bold]. Reconfigure?"):
            return

    console.print(Panel.fit(
        "[bold cyan]getreskilled.ai[/bold cyan]\n[dim]Learning platform for the AI era[/dim]",
        border_style="cyan",
        padding=(1, 4),
    ))
    console.print("\n[bold]First, choose your LLM provider:[/bold]\n")

    for i, p in enumerate(PROVIDERS, 1):
        console.print(f"  [bold]{i}.[/bold] {p['name']}")

    p_idx = IntPrompt.ask(
        "\nProvider",
        choices=[str(i) for i in range(1, len(PROVIDERS) + 1)],
    )
    provider = PROVIDERS[p_idx - 1]

    console.print(f"\n[bold]Choose a model:[/bold]\n")
    for i, (_, label) in enumerate(provider["models"], 1):
        console.print(f"  [bold]{i}.[/bold] {label}")

    m_idx = IntPrompt.ask(
        "\nModel",
        choices=[str(i) for i in range(1, len(provider["models"]) + 1)],
    )
    model_id, _ = provider["models"][m_idx - 1]

    api_key = None
    if provider["needs_key"]:
        console.print(f"\n[dim]Get your key → {provider['key_url']}[/dim]")
        api_key = Prompt.ask(f"Enter your {provider['name'].split()[0]} API key", password=True)

    config.save({
        "provider": provider["name"],
        "model": model_id,
        "api_key": api_key,
        "env_var": provider["env_var"],
    })

    console.print("\n[green]Setup complete![/green] Config saved to [dim]~/.reskilled/config.json[/dim]\n")
