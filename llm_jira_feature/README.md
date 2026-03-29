# Agentic Jira Story & Feature Creator

An AI-powered Streamlit application that automatically turns Excel sheets, meeting notes, or Confluence pages into actionable Jira features and stories.

## How It Works

1. **Connect to Jira** — Enter your Jira URL, email, and API token in the sidebar to authenticate.
2. **Configure LLM** — Point to your local LLM server (Ollama, vLLM, LM Studio, etc.) or any OpenAI-compatible endpoint.
3. **Choose Mode** — Select whether to generate **Features** or **Stories** from the dropdown.
4. **Provide Content** — Upload a CSV/Excel file, scrape a Confluence/web page, or paste text manually.
5. **Generate** — The AI analyzes your content and produces structured cards with titles, descriptions, and acceptance criteria.
6. **Review & Create** — Select a Jira project and issue type, review the cards, then create them individually or in bulk.
7. **Export** — Download a CSV of all created issues for record-keeping.

## Prerequisites

- Python 3.10+
- A Jira Cloud instance with an [API token](https://id.atlassian.com/manage-profile/security/api-tokens)
- A running LLM server (e.g., Ollama on port 12434) or any OpenAI-compatible API

## Setup

### 1. Clone and configure

```bash
git clone <repo-url>
cd Jira_features_creation
cp .env.example .env
```

Edit `.env` with your credentials:

```
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token
LLM_BASE_URL=http://localhost:12434/v1
LLM_MODEL=ai/llama3.2
```

### 2. Run

#### Option A: Docker (Recommended)

```bash
docker-compose up --build
```

Open http://localhost:8501

> **Note:** If your LLM runs on the host machine, use `http://host.docker.internal:12434/v1` as the LLM Base URL.

#### Option B: Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501

## Project Structure

```
├── app.py              # Streamlit UI — sidebar config, content input, generation, review
├── jira_client.py      # Jira REST API wrapper (connect, projects, issue types, create)
├── llm_agent.py        # LLM integration for generating features/stories
├── scraper.py          # URL/Confluence scraping and CSV/Excel parsing
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container image
├── docker-compose.yml  # One-command Docker startup
├── .env.example        # Environment variable template
└── Skill.md            # Detailed usage guide
```

## Usage

### Generating Features

1. Select **Features** from the Creation Mode dropdown.
2. Upload a CSV/Excel file — the app reads the first three columns from each row.
3. Click **Generate Jira Features**.
4. Review the generated cards (Feature Name, Description, Acceptance Criteria).
5. Select a Jira project and issue type, then create individually or use **Bulk Create Selected**.

### Generating Stories

1. Select **Stories** from the Creation Mode dropdown.
2. Provide content via file upload, URL scraping, or manual paste.
3. Click **Generate Jira Stories**.
4. Review the generated cards (Summary, Description, Acceptance Criteria).
5. Create in Jira and export the results to CSV.

### Confluence Scraping

Paste a Confluence page URL and the app will automatically use your Jira credentials to authenticate and extract the page content.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Cannot connect to Jira | Verify your API token is active and the URL is correct |
| LLM not responding | Ensure your LLM server is running on the configured port |
| Docker network error | Use `http://host.docker.internal:12434/v1` as the LLM Base URL |
| File upload fails | Ensure the file is CSV (.csv) or Excel (.xlsx, .xls) format |
