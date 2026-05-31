"""Nibble Orchestrator — Linear GraphQL client.

Polls Linear for issues in eligible states, transitions issues,
and posts comments.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)

LINEAR_API_URL = "https://api.linear.app/graphql"


@dataclass
class LinearIssue:
    id: str
    identifier: str  # e.g. "DN-15"
    title: str
    description: str
    state_name: str
    state_id: str
    labels: list[str]


class LinearClient:
    def __init__(self, api_key: str, team_id: Optional[str] = None):
        self.api_key = api_key
        self.team_id = team_id
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": api_key,
            "Content-Type": "application/json",
        })
        # Cache workflow state IDs
        self._state_ids: dict[str, str] = {}

    def _query(self, query: str, variables: Optional[dict] = None) -> dict:
        """Execute a GraphQL query against Linear."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = self.session.post(LINEAR_API_URL, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise RuntimeError(f"Linear API error: {data['errors']}")
        return data["data"]

    def resolve_team_id(self) -> str:
        """Get the first team ID if not already set."""
        if self.team_id:
            return self.team_id
        data = self._query("{ teams { nodes { id name } } }")
        teams = data["teams"]["nodes"]
        if not teams:
            raise RuntimeError("No teams found in Linear workspace")
        self.team_id = teams[0]["id"]
        logger.info(f"Resolved team: {teams[0]['name']} ({self.team_id})")
        return self.team_id

    def get_workflow_states(self) -> dict[str, str]:
        """Get mapping of state name -> state ID for the team."""
        if self._state_ids:
            return self._state_ids
        team_id = self.resolve_team_id()
        data = self._query(
            """
            query($teamId: String!) {
                workflowStates(filter: { team: { id: { eq: $teamId } } }) {
                    nodes { id name }
                }
            }
            """,
            {"teamId": team_id},
        )
        for state in data["workflowStates"]["nodes"]:
            self._state_ids[state["name"]] = state["id"]
        return self._state_ids

    def poll_issues(self, states: list[str]) -> list[LinearIssue]:
        """Fetch issues in the given workflow states."""
        team_id = self.resolve_team_id()
        state_ids = self.get_workflow_states()
        target_state_ids = [
            state_ids[s] for s in states if s in state_ids
        ]
        if not target_state_ids:
            return []

        data = self._query(
            """
            query($teamId: String!, $stateIds: [String!]!) {
                issues(filter: {
                    team: { id: { eq: $teamId } }
                    state: { id: { in: $stateIds } }
                }) {
                    nodes {
                        id
                        identifier
                        title
                        description
                        state { id name }
                        labels { nodes { name } }
                    }
                }
            }
            """,
            {"teamId": team_id, "stateIds": target_state_ids},
        )
        issues = []
        for node in data["issues"]["nodes"]:
            issues.append(LinearIssue(
                id=node["id"],
                identifier=node["identifier"],
                title=node["title"],
                description=node.get("description") or "",
                state_name=node["state"]["name"],
                state_id=node["state"]["id"],
                labels=[l["name"] for l in node["labels"]["nodes"]],
            ))
        return issues

    def transition_issue(self, issue_id: str, target_state: str) -> None:
        """Move an issue to a different workflow state."""
        state_ids = self.get_workflow_states()
        if target_state not in state_ids:
            logger.error(f"Unknown state: {target_state}")
            return
        self._query(
            """
            mutation($issueId: String!, $stateId: String!) {
                issueUpdate(id: $issueId, input: { stateId: $stateId }) {
                    success
                }
            }
            """,
            {"issueId": issue_id, "stateId": state_ids[target_state]},
        )
        logger.info(f"Transitioned issue {issue_id} → {target_state}")

    def comment_on_issue(self, issue_id: str, body: str) -> None:
        """Post a comment on a Linear issue."""
        self._query(
            """
            mutation($issueId: String!, $body: String!) {
                commentCreate(input: { issueId: $issueId, body: $body }) {
                    success
                }
            }
            """,
            {"issueId": issue_id, "body": body},
        )
        logger.info(f"Commented on issue {issue_id}")
