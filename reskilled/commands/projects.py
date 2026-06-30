import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from reskilled import llm, storage, ui

app = typer.Typer(help="Project ideas and guided plans")
console = Console()

# Inspired by https://github.com/codecrafters-io/build-your-own-x
# Each entry: (label, key, detail)  — key=None means section separator
TOPICS = [
    # Systems & Infrastructure
    ("── Systems & Infra ──",  None,          ""),
    ("Operating System",       "os",          "bootloader, kernel, scheduler, memory management, filesystem"),
    ("Docker",                 "docker",      "Linux namespaces, cgroups, overlay filesystems, container runtime"),
    ("Shell",                  "shell",       "POSIX parsing, job control, piping, redirects, builtins"),
    ("Memory Allocator",       "allocator",   "malloc/free, free lists, slab allocator, garbage collection"),
    ("Emulator / VM",          "emulator",    "CHIP-8, Game Boy, x86, bytecode VM, instruction decoding"),

    # Networking & Web
    ("── Networking & Web ──",  None,         ""),
    ("Network Stack",          "network",     "TCP/IP from scratch, HTTP server, DNS resolver, TLS handshake"),
    ("Web Server",             "webserver",   "HTTP/1.1, request routing, virtual hosts, chunked transfer"),
    ("Web Browser",            "browser",     "HTML parser, CSS layout engine, DOM, JavaScript engine basics"),
    ("BitTorrent Client",      "bittorrent",  "P2P protocol, DHT, piece selection, choking/unchoking"),

    # Languages & Compilers
    ("── Languages & Compilers ──", None,     ""),
    ("Programming Language",   "lang",        "lexer, parser, AST, interpreter, bytecode compiler"),
    ("Regex Engine",           "regex",       "NFA/DFA construction, Thompson's algorithm, backtracking"),
    ("Template Engine",        "template",    "tokenizer, context-aware rendering, partials, filters"),

    # Data & Search
    ("── Data & Search ──",    None,          ""),
    ("Database",               "database",    "storage engine, B-tree/LSM-tree, WAL, query planner, transactions"),
    ("Search Engine",          "search",      "inverted index, TF-IDF, BM25, ranking, tokenization"),
    ("Git",                    "git",         "content-addressable storage, DAG, branching, merging, packfiles"),

    # AI & ML
    ("── AI & ML ──",          None,          ""),
    ("Neural Network",         "neural-net",  "backpropagation, CNNs, RNNs, transformers — from scratch in NumPy"),
    ("AI Model",               "ai-model",    "decision trees, SVMs, k-means, gradient boosting from scratch"),

    # Graphics & Games
    ("── Graphics & Games ──", None,          ""),
    ("3D Renderer",            "renderer",    "ray tracing, rasterization, shaders, BVH, global illumination"),
    ("Game",                   "game",        "game loop, ECS, physics, collision detection, tile maps"),
    ("Physics Engine",         "physics",     "rigid body dynamics, collision detection, constraint solver"),

    # Tools
    ("── Tools ──",            None,          ""),
    ("Text Editor",            "editor",      "gap buffer, rope data structure, syntax highlighting, modes"),
    ("Command-Line Tool",      "cli-tool",    "argument parsing, TUI, ANSI escape codes, streaming output"),
    ("Bot",                    "bot",         "event loops, state machines, NLP parsing, external API calls"),
    ("Blockchain",             "blockchain",  "proof-of-work, Merkle trees, P2P gossip, UTXO model"),

    # Custom
    ("──────────────────",     None,          ""),
    ("Other (custom topic)",   "other",       ""),
    ("← Back",                 "back",        ""),
]


def menu() -> None:
    while True:
        ui.header("reskilled › Projects", "Build it from scratch. Understand it forever.")

        choices = []
        for label, key, _ in TOPICS:
            if key is None:
                choices.append((label, None))  # labeled separator
            else:
                choices.append((label, key))

        choice = ui.select("What do you want to build?", choices)

        if not choice or choice == "back":
            break
        elif choice == "other":
            _start_custom()
        else:
            _start(choice)


@app.command("start")
def start(
    topic: str = typer.Option(None, "--topic", "-t", help="Topic key, e.g. database, shell, neural-net"),
):
    """Browse build-from-scratch project ideas."""
    if not topic:
        menu()
        return
    if topic == "other":
        _start_custom()
    else:
        _start(topic)


def _get_topic(key: str):
    for item in TOPICS:
        label, k, detail = item
        if k == key:
            return label, detail
    return None, None


def _start(topic_key: str) -> None:
    name, detail = _get_topic(topic_key)
    if not name:
        console.print(f"[red]Unknown topic: {topic_key}[/red]")
        return

    level = ui.select("Experience level", [
        ("Beginner",      "beginner"),
        ("Intermediate",  "intermediate"),
        ("Advanced",      "advanced"),
    ])
    if not level:
        return

    _generate_ideas(name, detail, level)


def _start_custom() -> None:
    topic_name = Prompt.ask("\nWhat do you want to build from scratch")
    if not topic_name.strip():
        return

    level = ui.select("Experience level", [
        ("Beginner",      "beginner"),
        ("Intermediate",  "intermediate"),
        ("Advanced",      "advanced"),
    ])
    if not level:
        return

    _generate_ideas(topic_name, topic_name, level)


def _generate_ideas(topic_name: str, topic_detail: str, level: str) -> None:
    prompt = f"""You are helping someone pick a "build your own X from scratch" project inspired by https://github.com/codecrafters-io/build-your-own-x.

Topic: {topic_name} ({topic_detail})
Experience level: {level}

Generate 5 concrete project ideas where the person builds this from scratch — no high-level libraries that do the hard work. The goal is deep understanding of internals.

For each project use this format:
**Project N: Build Your Own [Title]**
What you'll build: (1 sentence, specific)
Core concepts: (3-5 key things they'll implement themselves)
Reference to learn from: (a real spec, paper, or open source project to study)
Estimated time: ...
First commit: (the very first thing to implement)

Order from simplest to most ambitious. Be concrete."""

    console.print(f"\n[bold]Build Your Own {topic_name} — {level}[/bold]\n")
    plan = ui.stream_response(prompt, label="Generating ideas", max_tokens=2000)

    if Confirm.ask("\nGet a week-by-week plan for one of these?"):
        choice = ui.select("Which project?", [
            ("Project 1", 1),
            ("Project 2", 2),
            ("Project 3", 3),
            ("Project 4", 4),
            ("Project 5", 5),
        ])
        if choice:
            _plan(topic_name, choice, level, plan)


def _plan(topic: str, num: int, level: str, ideas_context: str) -> None:
    prompt = f"""Based on these "build from scratch" project ideas:
{ideas_context}

Create a detailed week-by-week implementation plan for Project {num} ({topic}, {level} level).

Include:
- Week-by-week breakdown with specific things to implement each week
- The exact data structures and algorithms to write from scratch
- What to read before starting (specs, papers, reference implementations)
- How to test each milestone
- How to make it portfolio-ready (README, architecture diagram, blog post angle)
- What NOT to implement yourself (where it's acceptable to use a library)"""

    console.print(f"\n[bold]Project {num} — Week-by-Week Plan[/bold]\n")
    full_plan = ui.stream_response(prompt, label="Planning", max_tokens=2500)

    storage.save_project(topic, full_plan)
    console.print("[dim]Plan saved to ~/.reskilled/[/dim]\n")
