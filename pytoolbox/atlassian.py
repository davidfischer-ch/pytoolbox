"""
Module related to managing projects with Atlassian's products.
"""
from __future__ import annotations

from collections.abc import ValuesView
from typing import Any

from jira import JIRA

__all__ = ['JiraProject']


class JiraProject(object):
    """A JIRA project class with a simple API leveraging the class :class:`jira.JIRA`."""

    def __init__(
        self,
        project: str | None = None,
        server: str | None = None,
        auth: tuple[str, str] | None = None,
        feature_type: str | None = None
    ) -> None:
        self.project = project
        self.server = server
        self.auth = auth
        self.feature_type = feature_type
        self._fields = self._jira = None

    @property
    def fields(self) -> list[dict[str, Any]]:
        """Return the list of fields, caching the result."""
        self._fields = self._fields or self.jira.fields()
        return self._fields

    @property
    def features(self) -> ValuesView:
        """Return all issues of the configured feature type."""
        count, issues = None, {}
        while count != len(issues):
            count = len(issues)
            issues.update({
                i.id: i for i in self.jira.search_issues(
                    f'project={self.project} AND issuetype="{self.feature_type}"',
                    startAt=count
                )
            })
        return issues.values()

    @property
    def jira(self) -> JIRA:
        """Return a lazily-initialized :class:`jira.JIRA` client."""
        self._jira = self._jira or JIRA(server=self.server, basic_auth=self.auth)
        return self._jira

    @property
    def versions(self) -> list:
        """Return all versions of the project."""
        return self.jira.project_versions(self.project)

    def get_field(self, name: str, fail: bool = True) -> dict[str, Any] | None:
        """Return the field definition matching the given name."""
        try:
            return next(f for f in self.fields if f['name'] == name)
        except StopIteration:
            if fail:
                raise
        return None

    def get_field_value(self, issue: Any, name: str, default: Any = None) -> Any:
        """Return the value of a named field on the given issue."""
        field_id = self.get_field(name)['id']
        field_value = getattr(issue.fields, field_id) or default
        return getattr(field_value, 'value', field_value)
