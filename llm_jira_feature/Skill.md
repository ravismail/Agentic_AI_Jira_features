# 🚀 Agentic Jira story and Feature creation 

Welcome! This guide will walk you through how to use the **Agentic Jira Story and Feature Creator** to automatically turn your excel sheet, meeting notes or Confluence pages into actionable Jira stories.

---

## 1. 🛠️ Getting Started

### Option A: Running with Docker (Recommended)
This runs the application in a clean, isolated container.
1. Open a terminal in the project folder.
2. Run the command:
   ```powershell
   docker-compose up --build
   ```
3. Open your browser and go to: **[http://localhost:8501](http://localhost:8501)**

### Option B: Running Locally
1. Install dependencies: `pip install -r requirements.txt`
2. Run the app: `streamlit run app.py`

---

## 2. ⚙️ Step-by-Step Usage

### Level 1: Configuration (Sidebar)
Before generating stories, set up your connections:
1. **Jira Settings**: 
   - Enter your **Jira URL** (e.g., `https://your-company.atlassian.net`).
   - Enter your **Email** and **API Token**.
   - Click **"Connect to Jira"**. You should see a success message.
2. **LLM Settings**: 
   - Verify the **openai or Local LLM Base URL** (defaults to port 12434 for your setup).
   - Verify the **Model Name** (e.g., `ai/llama3.2`).

---
### Level 2: Have a drop down to create Featres or Stories
1. **Select Type**: Choose whether you want to generate "Stories" or "Features" from the dropdown.
2. The rest of the process is the same, but the AI will tailor the output format accordingly.

---

### Level 3: Retrieve Content
Tell the Agent what content to analyze:
For Features, you can upload a CSV/Excel file with high-level requirements or product specs. For Stories, you can provide detailed meeting notes or Confluence pages.
1. **Excel Sheet**: Upload a CSV or Excel file with meeting notes or requirements.
   - Read the each row and columns from the uploaded file.
   - Get the 1st, 2nd and 3rd column and create features.
   - Click **"Upload and Scrape"**. 
For Stories, you can also use:
2. **URL Scraping**: 
   - Paste a link to a Confluence page or any web article.
   - Click **"Scrape Content"**.
3. **Manual Input**:
   - Choose this to paste raw meeting minutes or transcriptions directly.
   - Click **"Use Manual Notes"**.

---

### Level 3: Generate Feature or Stories
IF Features selected, the AI will analyze the uploaded file and brainstorm high-level features, complete with:
- **Feature Name** (The "Title")
- **Feature Description** (The "What and Why")
- **Acceptance Criteria** (Checklist for completion)
1. Click the **"✨ Generate Jira Features"** button.

IF Stories selected, the AI will analyze the uploaded file and brainstorm user stories, complete with:

1. Click the **"✨ Generate Jira Stories"** button.
2. The AI will analyze the text and brainstorm User Stories, complete with:
   - **Summary** (The "Title")
   - **Description** (The "Who, What, Why")
   - **Acceptance Criteria** (Checklist for completion)

---

### Level 4: Review & Create
1. **Select Project**: Choose the target Jira project from the dropdown.
2. **Select Issue Type**: Choose "Story", "Task", etc.
3. **Review Cards**: Look through the generated story cards.
4. **Create in Jira**: Click the **"Create Story"** button under any card you like.
5. **Success!**: You will see a green checkmark and a direct link to your new Jira issue.
6. **Bulk Create**: You can also select multiple cards and click **"Create Selected"** to create them all at once.
7. **list of created Features/Stories**: Export the list of created features/stories in a CSV file for record-keeping or sharing with your team.

---

## 💡 Pro Tips
- **Confluence Auth**: The scraper uses your Jira credentials automatically to fetch restricted Confluence pages.
- **Dark Mode**: The UI is designed to look premium in BOTH Light and Dark themes of Streamlit.
- **Docker Logs**: Logs are streamed to System Out, so you can watch progress in your terminal using `docker logs -f agentic-jira-app`.

---

## 🚑 Troubleshooting
- **White text?**: I've fixed the CSS! Just refresh your browser.
- **Can't connect?**: Ensure Your Jira API Token is active and your Ollama server is running on the specified port.
- **Network Error (Docker)**: If Ollama is on your host machine, use `http://host.docker.internal:12434/v1` as the Base URL.
