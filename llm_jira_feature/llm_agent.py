"""LLM integration for generating Jira features and stories."""

import json
import logging
import re

from openai import OpenAI

logger = logging.getLogger("llm_agent")


FEATURE_SYSTEM_PROMPT = """You are an expert Product Manager. Analyze the provided content and extract high-level Features for a Jira board.

For each feature, provide:
1. Feature Name - a concise title
2. Description - what the feature does and why it matters
3. Acceptance Criteria - a checklist of conditions for completion

Return ONLY a JSON object in this exact format, with no other text:
{"features": [{"name": "...", "description": "...", "acceptance_criteria": ["criterion 1", "criterion 2"]}]}
"""

STORY_SYSTEM_PROMPT = """You are an expert Agile Product Owner. Analyze the provided content and extract actionable User Stories.

For each story, provide:
1. Summary - a concise title
2. Description - in the format "As a [user], I want [goal] so that [benefit]"
3. Acceptance Criteria - conditions that must be met for the story to be complete

Return ONLY a JSON object in this exact format, with no other text:
{"stories": [{"summary": "...", "description": "...", "acceptance_criteria": ["criterion 1", "criterion 2"]}]}
"""


class LLMAgent:
    """Generates Jira features and stories using an OpenAI-compatible LLM API."""

    def __init__(self, base_url: str, model: str, api_key: str = None):
        self.model = model
        self.client = OpenAI(base_url=base_url, api_key=api_key or "not-needed")

    def _call_llm(self, system_prompt: str, user_content: str) -> str:
        """Send a chat completion request and return the response text."""
        logger.info("Calling LLM model=%s, content_length=%d", self.model, len(user_content))
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
        )
        result = response.choices[0].message.content
        logger.info("LLM response received: %d chars", len(result))
        logger.debug("LLM raw response: %s", result[:500])
        return result

    def _parse_json(self, text: str) -> dict:
        """Extract and parse JSON from LLM response, handling markdown fences."""
        cleaned = text.strip()
        # Remove markdown code fences
        cleaned = re.sub(r"```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"```\s*$", "", cleaned)
        cleaned = cleaned.strip()

        # Find JSON boundaries
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]

        return json.loads(cleaned)

    def generate_features(self, content: str) -> list[dict]:
        """Generate feature cards from content."""
        logger.info("Generating features from %d chars of content", len(content))
        raw = self._call_llm(FEATURE_SYSTEM_PROMPT, content)
        parsed = self._parse_json(raw)
        features = parsed.get("features", [])
        for f in features:
            f.setdefault("name", "Untitled Feature")
            f.setdefault("description", "")
            f.setdefault("acceptance_criteria", [])
        logger.info("Parsed %d features", len(features))
        return features

    def generate_stories(self, content: str) -> list[dict]:
        """Generate user story cards from content."""
        logger.info("Generating stories from %d chars of content", len(content))
        raw = self._call_llm(STORY_SYSTEM_PROMPT, content)
        parsed = self._parse_json(raw)
        stories = parsed.get("stories", [])
        for s in stories:
            s.setdefault("summary", "Untitled Story")
            s.setdefault("description", "")
            s.setdefault("acceptance_criteria", [])
        logger.info("Parsed %d stories", len(stories))
        return stories
