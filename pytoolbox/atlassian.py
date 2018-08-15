# -*- encoding: utf-8 -*-

"""
Module related to managing projects with Atlassian's products.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from jira import JIRA

from . import module

_all = module.All(globals())


class JiraProject(object):
    """A JIRA project class with a simple API leveraging the class :class:`jira.JIRA`."""

    def __init__(self, project=None, server=None, auth=None, feature_type=None):
        self.project = project
        self.server = server
        self.auth = auth
        self.feature_type = feature_type
        self._fields = self._jira = None

    @property
    def fields(self):
        self._fields = self._fields or self.jira.fields()
        return self._fields

    @property
    def features(self):
        count, issues = None, {}
        while count != len(issues):
            count = len(issues)
            issues.update({
                i.id: i for i in self.jira.search_issues(
                    'project={0.project} AND issuetype="{0.feature_type}"'.format(self),
                    startAt=count
                )
            })
        return issues.itervalues()

    @property
    def jira(self):
        self._jira = self._jira or JIRA(server=self.server, basic_auth=self.auth)
        return self._jira

    @property
    def versions(self):
        return self.jira.project_versions(self.project)

    def get_field(self, name, fail=True):
        try:
            return next(f for f in self.fields if f['name'] == name)
        except StopIteration:
            if fail:
                raise

    def get_field_value(self, issue, name, default=None):
        field_id = self.get_field(name)['id']
        field_value = getattr(issue.fields, field_id) or default
        return getattr(field_value, 'value', field_value)


__all__ = _all.diff(globals())
