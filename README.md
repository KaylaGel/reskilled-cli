<p align="center">
  <img src="reskilled-logo.svg" alt="reskilled" width="220" />
</p>

**getreskilled.ai** — Learning platform for the AI era.

An open source CLI that helps you build a resume, get feedback, discover projects, and find communities — all from your terminal.

```
$ reskilled

  ╭──────────────────────────────────╮
  │  getreskilled.ai                 │
  │  Learning platform for the AI era│
  ╰──────────────────────────────────╯

  ○ No resume yet

❯ Resume
  Projects
  Network
  Exit
```

---

## Install

[uv](https://docs.astral.sh/uv/) is the recommended way to install reskilled. It handles Python and the virtual environment automatically.

```bash
# Install uv (if you don't have it)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**From PyPI** (once published):
```bash
uv tool install reskilled
```

**From source** (right now):
```bash
git clone https://github.com/getreskilled/reskilled-cli
cd reskilled-cli
uv venv                        # creates .venv in the project folder
source .venv/bin/activate      # Windows: .venv\Scripts\activate
uv pip install --editable .
reskilled
```

> **Prefer pip?** `pip install reskilled` works too (Python 3.11+ required).

---

## Setup

On first launch, `reskilled` walks you through a one-time setup — choose your provider and paste your API key:

```
Choose your LLM provider:

❯ Anthropic
  OpenAI
  Google Gemini
  Groq  (free tier available)
  Ollama  (local, completely free)
```

Config is stored at `~/.reskilled/config.json`. To change providers later:

```bash
reskilled setup
reskilled setup --force   # skip confirmation prompt
```

### Supported providers

| Provider | Models | Get a key |
|---|---|---|
| Anthropic | claude-sonnet-4-6, claude-opus-4-8, claude-haiku-4-5 | [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| OpenAI | gpt-4o, gpt-4o-mini | [platform.openai.com](https://platform.openai.com/api-keys) |
| Google Gemini | gemini-2.0-flash, gemini-1.5-pro | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| Groq | llama-3.3-70b, mixtral-8x7b | [console.groq.com](https://console.groq.com/keys) |
| Ollama | llama3.2, mistral, codellama | No key — [install ollama](https://ollama.ai) |

---

## Features

### Resume

Build, refine, and export your resume — fully locally, with AI assistance.

`reskilled` → **Resume**

```
reskilled › Resume

❯ Create resume
  Update resume
  Talk through experience
  Get feedback
  ATS check
  Apply to role
  View resume
  Export resume
  ← Back
```

**Create / Update**  
Guided Q&A builds your resume from scratch, or import an existing document:
- **Resume PDF** — paste a file path, content is extracted and reformatted
- **LinkedIn PDF export** — LinkedIn → Me → View Profile → More → Save to PDF

**Talk through experience**  
AI interview that digs into what you actually did. Select a role from your existing resume, review its current bullets, then have a back-and-forth conversation — the AI asks follow-up questions until it has enough detail to write strong, specific bullets. You choose which new bullets to merge back.

**Get feedback**  
Paste a job description and get targeted critique of your resume against that specific role.

**ATS check**  
Get an ATS compatibility report. Quick wins are extracted and numbered — apply all of them, pick specific ones, or skip.

**Apply to role**  
Tailors your resume for a specific job posting by rewriting it to match the role's language and requirements.

**View resume**  
Scrollable full-screen preview of your current resume in the terminal.

**Export resume**  
Three export formats, all saved to the current working directory:
- **Markdown** — `.md` file, ready to commit or paste anywhere
- **Harvard format** — AI reformats to the clean Harvard one-page style, saved as `resume_harvard.md`
- **PDF** — rendered with proper headings, bold, and italic; saved as `<yourname>.pdf`

---

### Projects

Build things from scratch to understand how they really work — inspired by [build-your-own-x](https://github.com/codecrafters-io/build-your-own-x).

`reskilled` → **Projects**

Pick a category and experience level. You'll get 5 "build your own X" project ideas with the core concepts to implement, reference material to study, and a first commit to make. Optionally get a full week-by-week plan for the one you choose.

**Categories:**

| Systems & Infra | Networking & Web | Languages & Compilers |
|---|---|---|
| Operating System | Network Stack | Programming Language |
| Docker | Web Server | Regex Engine |
| Shell | Web Browser | Template Engine |
| Memory Allocator | BitTorrent Client | |
| Emulator / VM | | |

| Data & Search | AI & ML | Graphics & Games | Tools |
|---|---|---|---|
| Database | Neural Network | 3D Renderer | Text Editor |
| Search Engine | AI Model | Game | Command-Line Tool |
| Git | | Physics Engine | Bot |
| | | | Blockchain |

Or enter **Other** to specify any custom topic.

---

### Network

Find events and communities on Meetup, Luma, and Eventbrite.

`reskilled` → **Network**

**Platforms:**
- **Meetup** — local tech groups and recurring events
- **Luma** — curated tech events and communities
- **Eventbrite** — workshops, conferences, and professional events

Enter a topic, get 5 AI-optimized search terms, pick one, and the relevant event page opens in your browser.

---

## Data & privacy

Everything is stored locally:

| Path | Contents |
|---|---|
| `~/.reskilled/config.json` | Provider, model, API key |
| `~/.reskilled/resume.md` | Your current resume |
| `~/.reskilled/resume_history/` | Previous resume versions (auto-archived on each save) |
| `~/.reskilled/projects/` | Project plans as markdown files |

No data is sent anywhere except your chosen LLM provider's API.

---

## Contributing

The install steps above (from source) are all you need to get a dev environment running.

PRs welcome. Open an issue first for large changes.

---

## Roadmap

- [ ] Certifications tracker
- [ ] Course recommendations by skill gap
- [ ] RAG over your own notes and courses
- [ ] More community platforms (Discord, Reddit)
- [ ] Cover letter generator
- [ ] Interview prep mode

---

## License

MIT — see [LICENSE](LICENSE).
