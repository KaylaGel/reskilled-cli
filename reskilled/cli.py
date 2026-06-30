import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from reskilled import config, storage
from reskilled.commands import resume, projects, network
from reskilled import ui

app = typer.Typer(
    name="[re]skilled",
    help="getreskilled.ai — Learning platform for the AI era",
    no_args_is_help=False,
    add_completion=True,
)
app.add_typer(resume.app,   name="resume")
app.add_typer(projects.app, name="projects")
app.add_typer(network.app,  name="network")

console = Console()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is not None:
        return

    console.print(Panel.fit(
        Text.assemble(
            ("getreskilled.ai\n", "bold cyan"),
            ("Learning platform for the AI era", "dim"),
        ),
        border_style="cyan",
        padding=(1, 4),
    ))

    if not config.is_configured():
        from reskilled.commands.setup import run
        run()

    while True:
        has_resume = storage.resume_path().exists()
        resume_status = "[green]●[/green] Resume saved" if has_resume else "[dim]○ No resume yet[/dim]"
        console.print(f"\n  {resume_status}")

        choice = ui.select("reskilled", [
            ("Resume",   "resume"),
            ("Projects", "projects"),
            ("Network",  "network"),
            None,
            ("Exit",     "exit"),
        ])

        if not choice or choice == "exit":
            break
        elif choice == "resume":
            resume.menu()
        elif choice == "projects":
            projects.menu()
        elif choice == "network":
            network.menu()


@app.command("setup")
def setup_cmd(force: bool = typer.Option(False, "--force", "-f", help="Reconfigure even if already set up")):
    """Configure your LLM provider and API key."""
    from reskilled.commands.setup import run
    run(force=force)


if __name__ == "__main__":
    app()
