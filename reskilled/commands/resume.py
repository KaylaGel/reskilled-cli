import json
import re
import shutil
import typer
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from reskilled import llm, storage, ui
from reskilled.parser import extract_pdf, fetch_job_posting

app = typer.Typer(help="Resume builder and feedback")
console = Console()

_SYSTEM = (
    "You are an expert resume writer specializing in tech careers. "
    "You write resumes that sound like a real person wrote them — confident, direct, and specific. "
    "Rules you always follow:\n"
    "- Never use hyphens to join words (no 'cross-functional', 'fast-paced', 'results-driven', etc.)\n"
    "- No AI buzzwords: avoid 'leverage', 'utilize', 'spearhead', 'orchestrate', 'synergy', 'cutting-edge'\n"
    "- No filler phrases: avoid 'responsible for', 'helped to', 'worked on', 'assisted with'\n"
    "- Write in plain, active English — the kind a sharp human would actually use\n"
    "- Lead bullets with strong past-tense verbs: Built, Shipped, Reduced, Grew, Designed, Cut, Ran\n"
    "- Be specific and concrete; vague claims read as AI-generated\n"
    "- Vary sentence structure and bullet length so it reads naturally, not formulaic"
)

_INTERVIEW_SYSTEM = (
    "You are conducting a short interview to extract concrete, resume-worthy detail about one job, "
    "project, or accomplishment the candidate is describing. "
    "Ask exactly one focused, specific follow up question at a time, about scope, actions taken, "
    "tools used, obstacles overcome, or results and metrics. Keep questions short and conversational. "
    "Once you have enough concrete detail to write 3 to 6 strong, specific resume bullets, "
    "reply with exactly the single word READY and nothing else — no question, no extra text."
)

_MAX_INTERVIEW_TURNS = 6


def _format_age(dt: datetime) -> str:
    delta = datetime.now() - dt
    if delta.days == 0:
        hours = delta.seconds // 3600
        return "just now" if hours == 0 else f"{hours}h ago"
    if delta.days == 1:
        return "yesterday"
    if delta.days < 30:
        return f"{delta.days} days ago"
    return dt.strftime("%b %d")


def menu() -> None:
    while True:
        mtime = storage.resume_last_modified()
        subtitle = f"Last updated {_format_age(mtime)}" if mtime else "No resume saved yet"
        ui.header("reskilled › Resume", subtitle)

        has_resume = mtime is not None
        no_resume = "save a resume first"

        choice = ui.select("Resume", [
            ("Create resume",           "create"),
            ("Update resume",           "update",   None if has_resume else no_resume),
            ("Talk through experience", "talk"),
            ("Get feedback",            "feedback", None if has_resume else no_resume),
            ("ATS check",               "ats",      None if has_resume else no_resume),
            ("Apply to role",           "apply",    None if has_resume else no_resume),
            ("View resume",             "view",     None if has_resume else no_resume),
            ("Export resume",           "export",   None if has_resume else no_resume),
            None,
            ("← Back",                  "back"),
        ])

        if not choice or choice == "back":
            break
        elif choice == "create":
            _create()
        elif choice == "update":
            _update()
        elif choice == "talk":
            _talk()
        elif choice == "feedback":
            _feedback()
        elif choice == "ats":
            _ats()
        elif choice == "apply":
            _apply()
        elif choice == "view":
            _view()
        elif choice == "export":
            _export()


@app.command("create")
def create():
    """Create a resume from scratch with AI assistance."""
    _create()


@app.command("update")
def update():
    """Update your saved resume."""
    _update()


@app.command("talk")
def talk():
    """Talk through what you did and let AI turn it into resume bullets."""
    _talk()


@app.command("feedback")
def feedback():
    """Get AI feedback on your resume."""
    _feedback()


@app.command("ats")
def ats():
    """Run an ATS compatibility check on your resume."""
    _ats()


@app.command("apply")
def apply(url: str = typer.Argument(None, help="Job posting URL")):
    """Tailor your resume for a specific role."""
    _apply(url)


@app.command("view")
def view():
    """Print your saved resume to the terminal."""
    _view()


@app.command("export")
def export(
    path: str = typer.Argument(None, help="Destination path"),
    harvard: bool = typer.Option(False, "--harvard", help="Export in Harvard style (default: ./resume_harvard.md)"),
    pdf: bool = typer.Option(False, "--pdf", help="Export as PDF (default: ./resume.pdf)"),
):
    """Export your resume to a file."""
    if harvard:
        _export_harvard(path)
    elif pdf:
        _export_pdf(path)
    else:
        _export(path)


# ── internal helpers ──────────────────────────────────────────────────────────

def _create() -> None:
    console.print()
    choice = ui.select("Start from", [
        ("Import a resume PDF",          "pdf"),
        ("Import a LinkedIn PDF export", "linkedin"),
        ("Start from scratch",           "scratch"),
    ])
    if not choice:
        return

    if choice in ("pdf", "linkedin"):
        _create_from_pdf(2 if choice == "linkedin" else 1)
    else:
        _create_from_scratch()


def _create_from_pdf(source: int) -> None:
    if source == 2:
        console.print(
            "\n[dim]To export your LinkedIn profile: LinkedIn → Me → View Profile → More → Save to PDF[/dim]"
        )
    path = Prompt.ask("\nPath to PDF")

    try:
        with ui.thinking("Reading PDF"):
            raw_text = extract_pdf(path)
    except FileNotFoundError as e:
        console.print(f"\n[red]{e}[/red]")
        return

    label = "LinkedIn profile" if source == 2 else "resume"
    target = Prompt.ask("\nRole you're targeting")
    extra  = Prompt.ask("Anything to add or emphasise [dim](optional)[/dim]", default="")

    prompt = f"""You are given the raw text of a {label}. Use it to create a polished resume tailored for a {target} role.

Preserve all real experience, education, skills, and dates. Do not invent specifics. \
Write so it sounds like a real person wrote it — direct, specific, no corporate filler. \
Return only the resume in clean markdown, no commentary.

{f"Additional notes from the candidate: {extra}" if extra else ""}

--- {label.upper()} TEXT ---
{raw_text}"""

    console.print()
    result = ui.stream_response(prompt, system=_SYSTEM, label="Building your resume", max_tokens=3000)

    storage.save_resume(result)
    console.print("[green]Resume saved.[/green] Run [bold]reskilled resume update[/bold] to refine it.\n")


def _create_from_scratch() -> None:
    console.print("\n[dim]Answer a few questions and I'll write a polished draft.[/dim]\n")

    name     = Prompt.ask("Full name")
    email    = Prompt.ask("Email")
    phone    = Prompt.ask("Phone [dim](optional)[/dim]", default="")
    location = Prompt.ask("Location [dim](city, country)[/dim]")
    linkedin = Prompt.ask("LinkedIn URL [dim](optional)[/dim]", default="")
    github   = Prompt.ask("GitHub URL [dim](optional)[/dim]", default="")
    target   = Prompt.ask("\nRole you're targeting")

    console.print("\n[bold]Work Experience[/bold] [dim]— press Enter on title to stop[/dim]")
    experiences = []
    while True:
        title = Prompt.ask("Job title", default="")
        if not title:
            break
        company = Prompt.ask("Company")
        period  = Prompt.ask("Period [dim](e.g. Jan 2022 – Present)[/dim]")
        console.print("Key accomplishments [dim](blank line to stop)[/dim]:")
        bullets: list[str] = []
        while True:
            b = Prompt.ask("  •", default="")
            if not b:
                break
            bullets.append(b)
        experiences.append({"title": title, "company": company, "period": period, "bullets": bullets})

    console.print("\n[bold]Education[/bold] [dim]— press Enter on degree to stop[/dim]")
    education = []
    while True:
        degree = Prompt.ask("Degree", default="")
        if not degree:
            break
        school = Prompt.ask("School")
        year   = Prompt.ask("Graduation year")
        education.append({"degree": degree, "school": school, "year": year})

    skills = Prompt.ask("\nKey skills [dim](comma-separated)[/dim]")

    contact_lines = [f"{name} | {email}"]
    if phone:    contact_lines[0] += f" | {phone}"
    if location: contact_lines[0] += f" | {location}"
    if linkedin: contact_lines.append(f"LinkedIn: {linkedin}")
    if github:   contact_lines.append(f"GitHub: {github}")

    exp_text = "\n".join(
        f"- {e['title']} at {e['company']} ({e['period']})\n"
        + "\n".join(f"  • {b}" for b in e["bullets"])
        for e in experiences
    ) or "None provided"

    edu_text = "\n".join(
        f"- {e['degree']}, {e['school']} ({e['year']})" for e in education
    ) or "None provided"

    prompt = f"""Create a polished, ATS-optimized resume for a {target} role.

Contact:
{chr(10).join(contact_lines)}

Experience:
{exp_text}

Education:
{edu_text}

Skills: {skills}

Format in clean markdown. Quantify where context allows. Do not invent specifics. \
Write so it sounds like a real person — not a template, not an AI. Return only the resume, no commentary."""

    console.print()
    result = ui.stream_response(prompt, system=_SYSTEM, label="Building your resume", max_tokens=3000)

    storage.save_resume(result)
    console.print("[green]Resume saved.[/green] Run [bold]reskilled resume update[/bold] to refine it.\n")


def _apply(url: str | None = None) -> None:
    existing = storage.latest_resume()
    if not existing:
        console.print("[yellow]No resume found. Run `reskilled resume create` first.[/yellow]")
        return

    if not url:
        url = Prompt.ask("\nJob posting URL")

    job_text = ""
    try:
        with ui.thinking("Fetching job posting"):
            job_text = fetch_job_posting(url)
    except Exception:
        pass

    if not job_text:
        console.print(
            "[yellow]Could not fetch page content (likely JS-rendered).[/yellow]\n"
            "Paste the job description below, then press [bold]Ctrl+D[/bold]:\n"
        )
        lines: list[str] = []
        try:
            while True:
                lines.append(input())
        except EOFError:
            pass
        job_text = "\n".join(lines)
        if not job_text.strip():
            console.print("[red]No job description provided.[/red]")
            return

    company = Prompt.ask("Company name")
    role    = Prompt.ask("Role title")
    notes   = Prompt.ask("Anything to highlight or adjust [dim](optional)[/dim]", default="")

    prompt = f"""Tailor this resume for the specific role below.

- Reorder and emphasise experience most relevant to this role
- Mirror key terms from the job posting naturally, not robotically (for ATS)
- Adjust the summary to speak directly to this role
- Keep all facts accurate — do not invent anything
- Write so it sounds like a real person — no hyphens joining words, no buzzwords, no filler phrases
{f"- Candidate notes: {notes}" if notes else ""}
- Return only the full tailored resume in clean markdown, no commentary

--- RESUME ---
{existing}

--- JOB POSTING ---
{job_text[:6000]}"""

    console.print()
    result = ui.stream_response(prompt, system=_SYSTEM, label=f"Tailoring for {role}", max_tokens=3000)

    path = storage.save_application(company, role, result)
    console.print(f"\n[green]Saved →[/green] [bold]{path.resolve()}[/bold]")
    console.print("[dim]Master resume unchanged → ~/.reskilled/resume.md[/dim]")


def _view() -> None:
    content = storage.latest_resume()
    if not content:
        console.print("[yellow]No resume found. Run `reskilled resume create` first.[/yellow]")
        return
    with console.pager(styles=True):
        console.print(Markdown(content))


def _export(path: str | None = None) -> None:
    if not storage.resume_path().exists():
        console.print("[yellow]No resume found. Run `reskilled resume create` first.[/yellow]")
        return

    fmt = ui.select("Export format", [
        ("Markdown — your resume as-is",        "md"),
        ("Harvard style — AI reformats layout", "harvard"),
        ("PDF — print-ready",                   "pdf"),
    ])
    if not fmt:
        return

    if fmt == "harvard":
        _export_harvard(path)
    elif fmt == "pdf":
        _export_pdf(path)
    else:
        dest = Path(path).expanduser() if path else Path.cwd() / "resume.md"
        shutil.copy(storage.resume_path(), dest)
        console.print(f"[green]Exported to[/green] {dest}")


def _export_harvard(path: str | None = None) -> None:
    content = storage.latest_resume()
    if not content:
        return

    prompt = f"""Reformat this resume into Harvard resume style.

Harvard style rules:
- Name centered at the top; contact details (email, phone, location, LinkedIn/GitHub) on one or two lines below it
- Section headers bold and consistently cased: Experience, Education, Skills
- Each role on its own line: Job Title, Employer — Location (dates right-aligned or clearly placed)
- Bullet points under each role start with a strong past-tense action verb
- Education: Degree, Institution, Graduation Year; honors or GPA only if notable
- Skills grouped by category (e.g. Languages, Frameworks, Tools)
- Clean minimal markdown — no horizontal rules, no excessive blank lines, consistent spacing throughout

Return only the reformatted resume in clean markdown, no commentary.

--- CURRENT RESUME ---
{content}"""

    console.print()
    result = ui.stream_response(prompt, system=_SYSTEM, label="Reformatting to Harvard style", max_tokens=3000)

    dest = Path(path).expanduser() if path else Path.cwd() / "resume_harvard.md"
    dest.write_text(result)
    console.print(f"\n[green]Harvard-style resume exported to[/green] [bold]{dest}[/bold]")


def _pdf_sanitize(text: str) -> str:
    """Replace non-Latin-1 characters with safe ASCII equivalents."""
    subs = {
        "—": " - ", "–": "-", "‒": "-", "‑": "-",
        "‘": "'",   "’": "'",
        "“": '"',   "”": '"',
        "•": "-",   "·": "-",
        "…": "...", " ": " ",
    }
    for ch, rep in subs.items():
        text = text.replace(ch, rep)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _render_resume_pdf(text: str, pdf) -> None:
    """Render sanitized markdown resume text directly into an FPDF instance."""
    lm = pdf.l_margin
    W  = pdf.w - lm - pdf.r_margin
    LH = 5  # body line height in mm

    def clean(s: str) -> str:
        """Strip all markdown markers, keep text."""
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)  # links
        s = re.sub(r"`([^`]+)`", r"\1", s)               # inline code
        s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)         # **bold**
        s = re.sub(r"\*([^*]+)\*", r"\1", s)             # *italic*
        return s.strip()

    # Strip wrapping code fence (```markdown ... ```)
    lines = [ln.rstrip() for ln in text.splitlines()]
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]

    for raw in lines:
        s = raw.strip()
        if not s or s.startswith("```"):
            continue

        # H1 — name
        if s.startswith("# "):
            pdf.set_x(lm)
            pdf.set_font("Helvetica", "B", 22)
            pdf.multi_cell(W, 9, clean(s[2:]), align="L")
            pdf.ln(1)

        # H2 — section header with underline rule
        elif s.startswith("## "):
            pdf.ln(6)
            pdf.set_x(lm)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(W, LH, clean(s[3:]), align="L", new_x="LMARGIN", new_y="NEXT")
            y = pdf.get_y()
            pdf.set_draw_color(40, 40, 40)
            pdf.set_line_width(0.3)
            pdf.line(lm, y, lm + W, y)
            pdf.set_xy(lm, y + 3)

        # H3 — job title / entry header (bold)
        elif s.startswith("### "):
            pdf.ln(3)
            pdf.set_x(lm)
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(W, LH, clean(s[4:]), align="L")

        # Bullet point
        elif s.startswith("- ") or s.startswith("* "):
            body = clean(s[2:])
            pdf.set_x(lm + 3)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(5, LH, "-", ln=False)
            pdf.set_x(lm + 8)
            pdf.multi_cell(W - 8, LH, body, align="L")
            pdf.set_x(lm)

        # *italic* line — dates, subtitles (not **bold**)
        elif s.startswith("*") and s.endswith("*") and not s.startswith("**"):
            pdf.set_x(lm)
            pdf.set_font("Helvetica", "I", 9)
            pdf.multi_cell(W, LH, clean(s), align="L")

        # **bold** standalone line — company names, awards
        elif s.startswith("**") and s.endswith("**"):
            pdf.set_x(lm)
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(W, LH, clean(s[2:-2]), align="L")

        # Contact line or regular paragraph
        else:
            pdf.set_x(lm)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(W, LH, clean(s), align="L")


def _export_pdf(path: str | None = None) -> None:
    content = storage.latest_resume()
    if not content:
        return

    try:
        from fpdf import FPDF
    except ImportError:
        console.print("[red]Missing package. Install with: [bold]uv add fpdf2[/bold][/red]")
        return

    dest = Path(path).expanduser() if path else Path.cwd() / "resume.pdf"

    with ui.thinking("Generating PDF"):
        pdf = FPDF()
        pdf.set_margins(22, 22, 22)
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=22)
        _render_resume_pdf(_pdf_sanitize(content), pdf)
        pdf.output(str(dest))

    console.print(f"\n[green]PDF exported to[/green] [bold]{dest}[/bold]")


def _update() -> None:
    existing = storage.latest_resume()
    if not existing:
        console.print("[yellow]No saved resume found. Run `reskilled resume create` first.[/yellow]")
        return

    console.print("\n[bold]What would you like to change?[/bold]")
    changes = Prompt.ask("Describe changes")

    prompt = f"""Update this resume based on the requested changes. Return the full updated resume in markdown.

Current resume:
{existing}

Requested changes:
{changes}"""

    console.print()
    result = ui.stream_response(prompt, system=_SYSTEM, label="Updating your resume", max_tokens=3000)

    storage.save_resume(result)
    console.print("[green]Resume updated and saved.[/green]\n")


def _extract_experiences(resume_text: str) -> list[dict]:
    prompt = f"""List each distinct job, role, or project entry in this resume's Experience and Projects \
sections, along with its existing bullet points. Return ONLY a JSON array, no commentary, no markdown \
code fences, in exactly this shape:

[{{"label": "Title — Company", "bullets": ["bullet one", "bullet two"]}}]

Omit the company in the label if there is none. If an entry has no bullets, use an empty list. \
If there are no such entries, return [].

Resume:
{resume_text}"""
    with ui.thinking("Reading your resume"):
        raw = llm.complete(prompt, max_tokens=800)

    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return []
    if not isinstance(data, list):
        return []

    return [
        {
            "label": e["label"].strip(),
            "bullets": [b.strip() for b in e.get("bullets", []) if b.strip()],
        }
        for e in data
        if isinstance(e, dict) and e.get("label", "").strip()
    ]


def _transcript(messages: list[dict]) -> str:
    speakers = {"user": "Candidate", "assistant": "Interviewer"}
    return "\n".join(
        f"{speakers[m['role']]}: {m['content']}" for m in messages if m["role"] != "system"
    )


def _talk() -> None:
    existing_resume = storage.latest_resume()
    experiences = _extract_experiences(existing_resume) if existing_resume else []

    placement = ""
    existing_bullets: list[str] = []
    if experiences:
        choice = ui.select("Which experience do you want to talk through?", [
            (e["label"], i) for i, e in enumerate(experiences)
        ] + [
            None,
            ("Something new / not on my resume", "__new__"),
        ])
        if not choice:
            return
        if choice != "__new__":
            selected = experiences[choice]
            placement = selected["label"]
            existing_bullets = selected["bullets"]

    if existing_bullets:
        console.print(f"\n[dim]Current bullets for {placement}:[/dim]")
        for b in existing_bullets:
            console.print(f"  [dim]• {b}[/dim]")

    console.print("\n[bold]Let's talk through what you actually did.[/bold]")
    console.print(
        "[dim]Describe what happened in your own words. I'll ask follow up questions, "
        "then write resume bullets from it. Press Enter on an empty answer to stop early.[/dim]\n"
    )

    context = Prompt.ask(f"Tell me about {placement}" if placement else "What do you want to write about")
    if not context.strip():
        return
    if placement:
        context = f"This is about my role/project: {placement}. {context}"

    system = _INTERVIEW_SYSTEM
    if existing_bullets:
        system += (
            "\n\nThe resume already has these bullets for this role — don't ask about things already "
            "covered here, focus on filling gaps, adding detail, or surfacing new accomplishments:\n"
            + "\n".join(f"- {b}" for b in existing_bullets)
        )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": context},
    ]

    for _ in range(_MAX_INTERVIEW_TURNS):
        with ui.thinking("Thinking"):
            reply = llm.chat(messages, max_tokens=200)
        messages.append({"role": "assistant", "content": reply})

        if reply.strip().upper().rstrip(".") == "READY":
            messages.pop()
            break

        console.print(f"\n[cyan]?[/cyan] {reply}")
        answer = Prompt.ask("  →", default="")
        if not answer.strip():
            break
        messages.append({"role": "user", "content": answer})

    extra_context = ""
    if existing_bullets:
        extra_context = (
            "\n\nThe role already has these bullets — write new ones that add detail or cover new "
            "ground, don't just restate them:\n" + "\n".join(f"- {b}" for b in existing_bullets)
        )

    prompt = f"""Based on this interview about the candidate's experience, write 3 to 6 resume bullets \
capturing what they actually did.

Use strong past tense verbs, be specific and concrete, quantify where the conversation supports it. \
Do not invent details that were not mentioned. Return only the bullets in markdown, no heading, no commentary.{extra_context}

--- INTERVIEW ---
{_transcript(messages)}"""

    console.print()
    bullets = ui.stream_response(prompt, system=_SYSTEM, label="Writing bullets", max_tokens=600)

    if not existing_resume:
        console.print(
            "\n[yellow]No saved resume yet.[/yellow] "
            "Run [bold]Create resume[/bold] first, then come back here to fold these in.\n"
        )
        return

    if not Confirm.ask("\nMerge these into your saved resume?"):
        return

    if not placement:
        placement = Prompt.ask(
            "Which role or project are these for [dim](e.g. 'Backend Engineer at Acme')[/dim]", default=""
        )

    merge_prompt = f"""Update this resume by incorporating the new bullets below. Place them under the \
matching existing experience entry{f" ({placement})" if placement else ""} if one exists, or add a new \
entry if none matches. Merge them with any existing bullets for that entry — keep the strongest points, \
remove redundancy, and don't repeat the same accomplishment twice. Return the full updated resume in markdown.

Current resume:
{existing_resume}

New bullets to incorporate:
{bullets}"""

    console.print()
    result = ui.stream_response(merge_prompt, system=_SYSTEM, label="Updating your resume", max_tokens=3000)

    storage.save_resume(result)
    console.print("[green]Resume updated and saved.[/green]\n")


def _feedback() -> None:
    existing = storage.latest_resume()
    if not existing:
        console.print("[yellow]No saved resume. Paste it below, then press Ctrl+D:[/yellow]\n")
        lines: list[str] = []
        try:
            while True:
                lines.append(input())
        except EOFError:
            pass
        existing = "\n".join(lines)
        if not existing.strip():
            console.print("[red]No resume provided.[/red]")
            return

    role = Prompt.ask("\nRole you're applying for")

    prompt = f"""Review this resume for a {role} role. Give specific, actionable feedback on:

1. Overall first impression
2. Weak or missing content
3. ATS optimization
4. Formatting and readability
5. Three concrete improvements to make right now

Resume:
{existing}"""

    console.print()
    ui.stream_response(prompt, system="You are an expert resume reviewer and career coach.", label="Analyzing")


def _ats() -> None:
    existing = storage.latest_resume()
    if not existing:
        console.print("[yellow]No saved resume found. Run `reskilled resume create` first.[/yellow]")
        return

    console.print()
    has_jd = ui.select("Do you have a job description to check against?", [
        ("Yes — paste or fetch a job posting", "yes"),
        ("No — general ATS check only",        "no"),
    ])
    if not has_jd:
        return

    job_section = ""
    if has_jd == "yes":
        url = Prompt.ask("\nJob posting URL [dim](or press Enter to paste)[/dim]", default="")
        job_text = ""
        if url.strip():
            try:
                with ui.thinking("Fetching job posting"):
                    job_text = fetch_job_posting(url)
            except Exception:
                pass
        if not job_text:
            if url.strip():
                console.print("[yellow]Could not fetch — paste the job description below, then Ctrl+D:[/yellow]\n")
            else:
                console.print("Paste the job description below, then [bold]Ctrl+D[/bold]:\n")
            lines: list[str] = []
            try:
                while True:
                    lines.append(input())
            except EOFError:
                pass
            job_text = "\n".join(lines).strip()
        if job_text:
            job_section = f"\n\n--- JOB DESCRIPTION ---\n{job_text[:5000]}"

    jd_instructions = (
        """- Keyword match: list keywords from the job description that are present and missing
- Role alignment: how well the resume speaks to this specific role"""
        if job_section else
        "- Keyword coverage: identify any gaps for a typical role in this field"
    )

    prompt = f"""Run a thorough ATS compatibility check on this resume.{job_section}

Structure your report with these sections:

**ATS Score** — give an overall score out of 100 with a one-line verdict

**Parsing risks** — anything that would confuse an ATS parser: tables, columns, headers/footers, \
special characters, graphics, non-standard section names, missing contact fields

**Keyword analysis**
{jd_instructions}

**Formatting** — date consistency, bullet style, section order, length

**Quick wins** — the 3 most impactful changes to make right now, each as a concrete action

Be direct and specific. Name the exact line or section when flagging an issue.

--- RESUME ---
{existing}"""

    console.print()
    report = ui.stream_response(
        prompt,
        system="You are an ATS expert and technical recruiter who reviews hundreds of resumes a week.",
        label="Running ATS check",
        max_tokens=2000,
    )

    # Extract the quick wins as a structured list
    with ui.thinking("Extracting quick wins"):
        raw_wins = llm.complete(
            f"""From this ATS report extract the "Quick wins" items. Return a JSON array of strings, \
one string per win, no numbering inside the strings. Return only the JSON array, no other text.

{report}""",
            max_tokens=400,
        )

    wins: list[str] = []
    cleaned = raw_wins.strip().strip("`")
    if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:].strip()
    try:
        parsed = json.loads(cleaned)
        wins = [w.strip() for w in parsed if isinstance(w, str) and w.strip()]
    except (json.JSONDecodeError, ValueError):
        wins = []

    if not wins:
        return

    console.print("\n[bold]Quick wins[/bold]")
    for i, w in enumerate(wins, 1):
        console.print(f"  [cyan]{i}.[/cyan] {w}")

    action = ui.select("\nImplement changes?", [
        ("Apply all",    "all"),
        ("Let me pick",  "pick"),
        ("Skip",         "skip"),
    ])
    if not action or action == "skip":
        return

    selected_wins = wins
    if action == "pick":
        indices = ui.multiselect("Select wins to implement", [(w, i) for i, w in enumerate(wins, 1)])
        if not indices:
            return
        selected_wins = [wins[i - 1] for i in indices]

    wins_text = "\n".join(f"{i}. {w}" for i, w in enumerate(selected_wins, 1))

    update_prompt = f"""Apply these specific improvements to this resume. Make only the changes \
described — don't alter anything else. Return the full updated resume in markdown.

Improvements to apply:
{wins_text}

--- RESUME ---
{existing}"""

    console.print()
    result = ui.stream_response(update_prompt, system=_SYSTEM, label="Applying changes", max_tokens=3000)
    storage.save_resume(result)
    console.print("[green]Resume updated and saved.[/green]\n")
