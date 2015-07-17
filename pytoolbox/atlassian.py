# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2015 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pytoolbox Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function, unicode_literals

from jira import JIRA

from . import module

_all = module.All(globals())


class JiraProject(object):

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
                    'project={0.project} AND issuetype="{0.feature_type}"'.format(self), startAt=count
                )
            })
        return issues.values()

    @property
    def jira(self):
        self._jira = self._jira or JIRA(server=self.server, basic_auth=self.auth)
        return self._jira

    @property
    def versions(self):
        return self.jira.project_versions(self.project)

    def get_field_value(self, issue, name, default=None):
        field_id = next(f for f in self.fields if f['name'] == name)['id']
        field_value = getattr(issue.fields, field_id) or default
        return getattr(field_value, 'value', field_value)

__all__ = _all.diff(globals())
