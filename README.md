# Agentic Workflow

A personal automation framework built on the **WAT architecture** — Workflows, Agents, Tools. AI handles orchestration and decision-making; deterministic Python scripts handle execution.

## How It Works

```
workflows/   →   Agent (Claude)   →   tools/
  (SOPs)       (reads & decides)    (executes)
```

- **Workflows** (`workflows/`): Markdown SOPs that define what to do, what inputs are needed, which tools to call, and how to handle edge cases.
- **Agent**: Claude reads the relevant workflow and coordinates execution — it doesn't do the work itself.
- **Tools** (`tools/`): Python scripts that do the actual work: API calls, data transforms, file operations.

## Project Structure

```
.
├── CLAUDE.md           # Agent operating instructions
├── workflows/          # Markdown SOPs (one per task type)
├── tools/              # Python execution scripts
├── .tmp/               # Disposable intermediates (gitignored)
├── .env                # Your API keys (never committed)
├── .env.example        # Template — copy to .env and fill in
├── requirements.txt    # Python dependencies
├── credentials.json    # Google OAuth credentials (gitignored)
└── token.json          # Google OAuth token (gitignored)
```

## Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd "Agentic Workflow"
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your API keys. This file is gitignored — never commit it.

### 5. Google OAuth (if using Sheets / Slides / Drive)

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Enable the APIs you need (Sheets, Slides, Drive).
3. Create OAuth 2.0 credentials and download as `credentials.json` into the project root.
4. The first time a Google tool runs it will open a browser for authorization and save `token.json` automatically.

## Running a Workflow

Tell Claude what you want to accomplish. Claude will:

1. Find and read the relevant workflow in `workflows/`
2. Identify the required inputs and tools
3. Execute the tools in sequence
4. Deliver outputs to the cloud service specified in the workflow (e.g. Google Sheets)

## Adding a New Tool

1. Create `tools/<tool_name>.py`
2. Read credentials/config from `.env` via `python-dotenv`
3. Accept inputs as CLI arguments or a simple config dict
4. Write outputs to `.tmp/` or directly to a cloud service
5. Reference the tool in the relevant workflow

## Adding a New Workflow

Create `workflows/<workflow_name>.md` with these sections:

- **Objective** — what this workflow accomplishes
- **Inputs** — what Claude needs before starting
- **Tools** — which scripts to call and in what order
- **Outputs** — what gets produced and where it goes
- **Edge Cases** — known failure modes and how to handle them

> Note: Don't create or overwrite workflows without checking with the agent first — these are living instructions.
