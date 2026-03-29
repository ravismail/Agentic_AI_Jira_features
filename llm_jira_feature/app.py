"""Agentic Jira Story & Feature Creator - Streamlit Application."""

import io
import logging
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from jira_client import JiraClient, JiraClientError
from llm_agent import LLMAgent
from scraper import ContentScraper

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("app")

# ---------------------------------------------------------------------------
# Page config & custom CSS
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Agentic Jira Creator",
    page_icon="🚀",
    layout="wide",
)

st.markdown(
    """
    <style>
    .card {
        border: 1px solid var(--secondary-background-color, #e0e0e0);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        background: var(--secondary-background-color, #f9f9fb);
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .card h4 { margin-top: 0; }
    .success-badge {
        background: #22c55e; color: white; padding: 4px 12px;
        border-radius: 6px; font-size: 0.85rem; font-weight: 600;
    }
    .fail-badge {
        background: #ef4444; color: white; padding: 4px 12px;
        border-radius: 6px; font-size: 0.85rem; font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
DEFAULTS = {
    "jira_client": None,
    "jira_connected": False,
    "jira_user": "",
    "projects": [],
    "issue_types": [],
    "content": "",
    "file_rows": [],
    "generated_items": [],
    "created_issues": [],
    "last_project_key": "",
}
for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ---------------------------------------------------------------------------
# Sidebar — Jira & LLM settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Jira Settings")
    jira_url = st.text_input("Jira URL", value=os.getenv("JIRA_URL", ""), placeholder="https://your-company.atlassian.net")
    jira_email = st.text_input("Email", value=os.getenv("JIRA_EMAIL", ""))
    jira_token = st.text_input("API Token", value=os.getenv("JIRA_API_TOKEN", ""), type="password")

    if st.button("Connect to Jira", use_container_width=True):
        if not all([jira_url, jira_email, jira_token]):
            st.error("Please fill in all Jira fields.")
        else:
            try:
                logger.info("Connecting to Jira at %s as %s", jira_url, jira_email)
                client = JiraClient(jira_url, jira_email, jira_token)
                user_info = client.connect()
                st.session_state.jira_client = client
                st.session_state.jira_connected = True
                st.session_state.jira_user = user_info["displayName"]
                st.session_state.projects = client.get_projects()
                logger.info("Jira connected — user: %s, projects: %d", user_info["displayName"], len(st.session_state.projects))
                st.success(f"Connected as **{user_info['displayName']}**")
            except JiraClientError as e:
                logger.error("Jira connection failed: %s", e)
                st.error(str(e))

    if st.session_state.jira_connected:
        st.info(f"Logged in as **{st.session_state.jira_user}**")

    st.divider()
    st.header("LLM Settings")
    llm_base_url = st.text_input(
        "LLM Base URL", value=os.getenv("LLM_BASE_URL", "http://localhost:12434/engines/v1"),
    )
    llm_model = st.text_input("Model Name", value=os.getenv("LLM_MODEL", "ai/llama3.2"))
    llm_api_key = None

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.title("Agentic Jira Story & Feature Creator")

creation_mode = st.selectbox("Creation Mode", ["Features", "Stories"])

# ---------------------------------------------------------------------------
# Section 1 — Content input
# ---------------------------------------------------------------------------
st.header("1. Provide Content")

scraper = ContentScraper()

tab_file, tab_url, tab_manual = st.tabs(["Upload File", "Scrape URL", "Manual Input"])

with tab_file:
    uploaded = st.file_uploader(
        "Upload CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        key="file_upload",
    )
    if uploaded:
        try:
            rows, col_names = scraper.parse_file(uploaded)
            st.session_state.file_rows = rows
            st.dataframe(pd.DataFrame(rows), use_container_width=True, height=250)
            if len(rows) == scraper.MAX_ROWS:
                st.warning(f"Showing first {scraper.MAX_ROWS} rows only.")
            if st.button("Use Uploaded Data", key="btn_file"):
                content = scraper.format_file_content(rows)
                st.session_state.content = content
                st.session_state.generated_items = []
                logger.info("File loaded: %s (%d rows)", uploaded.name, len(rows))
                st.success(f"Loaded {len(rows)} rows from **{uploaded.name}**.")
        except Exception as e:
            logger.error("File parse error: %s", e)
            st.error(f"File error: {e}")

with tab_url:
    url_input = st.text_input("Paste URL (Confluence or web page)", key="url_input")
    if st.button("Scrape Content", key="btn_url"):
        if not url_input:
            st.error("Please enter a URL.")
        else:
            try:
                logger.info("Scraping URL: %s", url_input)
                with st.spinner("Scraping..."):
                    text = scraper.scrape_url(url_input, jira_email, jira_token)
                st.session_state.content = text
                st.session_state.generated_items = []
                logger.info("Scrape complete: %d chars", len(text))
                with st.expander("Preview scraped content", expanded=False):
                    st.text(text[:3000])
                st.success(f"Scraped {len(text)} characters.")
            except Exception as e:
                logger.error("Scrape failed for %s: %s", url_input, e)
                st.error(f"Scrape error: {e}")

with tab_manual:
    manual_text = st.text_area("Paste meeting notes or requirements", height=250, key="manual_input")
    if st.button("Use Manual Notes", key="btn_manual"):
        if not manual_text.strip():
            st.error("Please enter some content.")
        else:
            st.session_state.content = manual_text.strip()
            st.session_state.generated_items = []
            st.success("Manual content loaded.")

# Show current content status
if st.session_state.content:
    st.caption(f"Content loaded ({len(st.session_state.content)} chars)")

# ---------------------------------------------------------------------------
# Section 2 — AI Generation
# ---------------------------------------------------------------------------
if st.session_state.content:
    st.header(f"2. Generate Jira {creation_mode}")

    if st.button(f"Generate Jira {creation_mode}", type="primary", use_container_width=True):
        try:
            logger.info("Generating %s via LLM (%s @ %s)", creation_mode, llm_model, llm_base_url)
            agent = LLMAgent(llm_base_url, llm_model, api_key=llm_api_key)
            with st.spinner(f"Generating {creation_mode.lower()}..."):
                if creation_mode == "Features":
                    items = agent.generate_features(st.session_state.content)
                else:
                    items = agent.generate_stories(st.session_state.content)
            st.session_state.generated_items = items
            logger.info("Generated %d %s", len(items), creation_mode.lower())
            st.success(f"Generated **{len(items)}** {creation_mode.lower()}.")
        except Exception as e:
            logger.error("LLM generation failed: %s", e, exc_info=True)
            st.error(f"LLM error: {e}")

# ---------------------------------------------------------------------------
# Section 3 — Review & Create in Jira
# ---------------------------------------------------------------------------
if st.session_state.generated_items:
    st.header("3. Review & Create in Jira")

    items = st.session_state.generated_items

    # Project & issue type selectors
    col_proj, col_type = st.columns(2)
    with col_proj:
        if st.session_state.projects:
            project_options = [f"{p['key']} - {p['name']}" for p in st.session_state.projects]
            selected_proj = st.selectbox("Jira Project", project_options, key="sel_project")
            project_key = selected_proj.split(" - ")[0]

            # Refresh issue types when project changes
            if project_key != st.session_state.last_project_key:
                st.session_state.last_project_key = project_key
                try:
                    st.session_state.issue_types = st.session_state.jira_client.get_issue_types(project_key)
                except JiraClientError as e:
                    st.error(str(e))
        else:
            st.warning("Connect to Jira first to select a project.")
            project_key = None

    with col_type:
        if st.session_state.issue_types:
            issue_type = st.selectbox("Issue Type", st.session_state.issue_types, key="sel_issuetype")
        else:
            issue_type = st.text_input("Issue Type", value="Story", key="manual_issuetype")

    # Render cards with checkboxes
    st.subheader(f"Generated {creation_mode}")

    def _toggle_all():
        val = st.session_state.select_all
        for idx in range(len(st.session_state.generated_items)):
            st.session_state[f"chk_{idx}"] = val

    st.checkbox("Select All", key="select_all", on_change=_toggle_all)

    selected_indices = []
    for i, item in enumerate(items):
        is_feature = creation_mode == "Features"
        title = item.get("name" if is_feature else "summary", "Untitled")
        desc = item.get("description", "")
        criteria = item.get("acceptance_criteria", [])

        with st.container():
            st.markdown(f'<div class="card">', unsafe_allow_html=True)
            col_check, col_content = st.columns([0.05, 0.95])
            with col_check:
                checked = st.checkbox("", key=f"chk_{i}", label_visibility="collapsed")
                if checked:
                    selected_indices.append(i)
            with col_content:
                st.markdown(f"#### {title}")
                st.markdown(desc)
                if criteria:
                    st.markdown("**Acceptance Criteria:**")
                    for ac in criteria:
                        st.markdown(f"- {ac}")

                # Individual create button
                if project_key and st.session_state.jira_connected:
                    if st.button(f"Create This Issue", key=f"create_{i}"):
                        ac_text = "\n".join(f"* {c}" for c in criteria)
                        full_desc = f"{desc}\n\n*Acceptance Criteria:*\n{ac_text}" if ac_text else desc
                        try:
                            logger.info("Creating issue: %s in %s", title, project_key)
                            result = st.session_state.jira_client.create_issue(
                                project_key, title, full_desc, issue_type,
                            )
                            st.session_state.created_issues.append(result)
                            logger.info("Issue created: %s", result["key"])
                            st.markdown(
                                f'<span class="success-badge">Created: '
                                f'<a href="{result["url"]}" target="_blank">{result["key"]}</a></span>',
                                unsafe_allow_html=True,
                            )
                        except JiraClientError as e:
                            logger.error("Issue creation failed: %s", e)
                            st.error(str(e))
            st.markdown("</div>", unsafe_allow_html=True)

    # Bulk create
    st.divider()
    if project_key and st.session_state.jira_connected:
        if st.button(
            f"Bulk Create Selected ({len(selected_indices)})",
            type="primary",
            disabled=len(selected_indices) == 0,
            use_container_width=True,
        ):
            is_feature = creation_mode == "Features"
            bulk_items = []
            for idx in selected_indices:
                item = items[idx]
                title = item.get("name" if is_feature else "summary", "Untitled")
                desc = item.get("description", "")
                criteria = item.get("acceptance_criteria", [])
                ac_text = "\n".join(f"* {c}" for c in criteria)
                full_desc = f"{desc}\n\n*Acceptance Criteria:*\n{ac_text}" if ac_text else desc
                bulk_items.append({"summary": title, "description": full_desc})

            logger.info("Bulk creating %d issues in %s", len(bulk_items), project_key)
            with st.spinner("Creating issues..."):
                results = st.session_state.jira_client.bulk_create_issues(
                    project_key, bulk_items, issue_type,
                )
            success_count = sum(1 for r in results if r["status"] == "success")
            logger.info("Bulk create done: %d/%d succeeded", success_count, len(results))

            for r in results:
                if r["status"] == "success":
                    st.session_state.created_issues.append(r)
                    st.markdown(
                        f'<span class="success-badge">Created: '
                        f'<a href="{r["url"]}" target="_blank">{r["key"]}</a> — {r["summary"]}</span>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<span class="fail-badge">Failed: {r["summary"]} — {r.get("error", "")}</span>',
                        unsafe_allow_html=True,
                    )

    # Export created issues
    if st.session_state.created_issues:
        st.divider()
        st.subheader("Created Issues")
        df_created = pd.DataFrame(st.session_state.created_issues)
        st.dataframe(df_created, use_container_width=True)
        csv_data = df_created.to_csv(index=False)
        st.download_button(
            "Export to CSV",
            data=csv_data,
            file_name="created_jira_issues.csv",
            mime="text/csv",
            use_container_width=True,
        )
