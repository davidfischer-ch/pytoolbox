"""Tests for the atlassian module."""

from __future__ import annotations

from unittest import mock

from jira import JIRA

from pytoolbox.atlassian import JiraProject


def test_features_returns_every_issue_on_jira_cloud() -> None:
    """On Jira Cloud, features returns every issue of the type, beyond its first search."""
    issues = [mock.Mock(id=str(number)) for number in range(3)]

    def enhanced_search_issues(_client, **kwargs):
        return issues if kwargs['maxResults'] is False else issues[:1]

    project = JiraProject(project='PRJ', feature_type='Feature')
    project._jira = JIRA.__new__(JIRA)  # pylint:disable=protected-access
    with (
        mock.patch.object(JIRA, '_is_cloud', new_callable=mock.PropertyMock, return_value=True),
        mock.patch.object(JIRA, 'enhanced_search_issues', autospec=True) as search,
    ):
        search.side_effect = enhanced_search_issues
        assert list(project.features) == issues
