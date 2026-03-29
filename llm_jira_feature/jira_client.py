"""Jira REST API wrapper using requests (no native C dependencies)."""

import logging

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger("jira_client")


class JiraClientError(Exception):
    """Custom exception for Jira client errors."""
    pass


class JiraClient:
    """Calls the Jira Cloud REST API directly via requests."""

    def __init__(self, url: str, email: str, api_token: str):
        self.url = url.rstrip("/")
        self.email = email
        self.auth = HTTPBasicAuth(email, api_token)
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.connected = False

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{self.url}/rest/api/3/{path}"
        logger.debug("GET %s params=%s", url, params)
        resp = requests.get(url, headers=self.headers, auth=self.auth, params=params, timeout=30)
        if not resp.ok:
            logger.error("GET %s failed (%d): %s", url, resp.status_code, resp.text)
            raise JiraClientError(f"Jira API error ({resp.status_code}): {resp.text}")
        return resp.json()

    def _post(self, path: str, json_body: dict) -> dict:
        url = f"{self.url}/rest/api/3/{path}"
        logger.debug("POST %s", url)
        resp = requests.post(url, headers=self.headers, auth=self.auth, json=json_body, timeout=30)
        if not resp.ok:
            logger.error("POST %s failed (%d): %s", url, resp.status_code, resp.text)
            raise JiraClientError(f"Jira API error ({resp.status_code}): {resp.text}")
        return resp.json()

    def connect(self) -> dict:
        """Verify credentials by fetching current user info."""
        try:
            logger.info("Connecting to Jira at %s", self.url)
            user = self._get("myself")
            self.connected = True
            logger.info("Authenticated as %s", user.get("displayName"))
            return {
                "displayName": user.get("displayName", self.email),
                "emailAddress": user.get("emailAddress", self.email),
            }
        except requests.RequestException as e:
            logger.error("Connection failed: %s", e)
            raise JiraClientError(f"Connection error: {e}") from e

    def get_projects(self) -> list[dict]:
        """Return list of accessible projects."""
        if not self.connected:
            raise JiraClientError("Not connected to Jira.")
        data = self._get("project", params={"orderBy": "name"})
        return [{"key": p["key"], "name": p["name"]} for p in data]

    def get_issue_types(self, project_key: str) -> list[str]:
        """Return available issue types for a project."""
        if not self.connected:
            raise JiraClientError("Not connected to Jira.")
        try:
            data = self._get(f"issue/createmeta/{project_key}/issuetypes")
            return [it["name"] for it in data.get("issueTypes", data.get("values", []))]
        except JiraClientError:
            # Fallback: fetch all issue types for the project
            data = self._get(f"issuetype/project", params={"projectId": project_key})
            return [it["name"] for it in data]

    def create_issue(
        self, project_key: str, summary: str, description: str, issue_type: str
    ) -> dict:
        """Create a single Jira issue and return its key and URL."""
        if not self.connected:
            raise JiraClientError("Not connected to Jira.")
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}],
                        }
                    ],
                },
                "issuetype": {"name": issue_type},
            }
        }
        result = self._post("issue", payload)
        key = result["key"]
        logger.info("Created issue %s: %s", key, summary)
        return {
            "key": key,
            "url": f"{self.url}/browse/{key}",
            "summary": summary,
        }

    def bulk_create_issues(
        self, project_key: str, issues: list[dict], issue_type: str
    ) -> list[dict]:
        """Create multiple issues. Each item needs 'summary' and 'description' keys."""
        results = []
        for item in issues:
            try:
                result = self.create_issue(
                    project_key=project_key,
                    summary=item["summary"],
                    description=item["description"],
                    issue_type=issue_type,
                )
                result["status"] = "success"
                results.append(result)
            except JiraClientError as e:
                results.append({
                    "summary": item["summary"],
                    "status": "failed",
                    "error": str(e),
                })
        return results
