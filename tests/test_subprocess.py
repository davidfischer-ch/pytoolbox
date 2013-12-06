# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
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

from nose.tools import assert_equal
from pytoolbox.unittest import mock_cmd
from pytoolbox.subprocess import cmd, screen_launch, screen_list, screen_kill
from pytoolbox.validation import validate_list


class TestSubprocess(object):

    def test_cmd(self):
        cmd_log = mock_cmd()
        cmd([u'echo', u'it seem to work'], log=cmd_log)
        assert_equal(cmd(u'cat missing_file', fail=False, log=cmd_log)[u'returncode'], 1)
        validate_list(cmd_log.call_args_list, [
                r"call\(u*\"Execute \[u*'echo', u*'it seem to work'\]\"\)",
                r"call\(u*'Execute cat missing_file'\)"])
        assert(cmd(u'my.funny.missing.script.sh', fail=False)[u'stderr'] != u'')
        result = cmd(u'cat {0}'.format(__file__))
        # There are at least 30 lines in this source file !
        assert(len(result[u'stdout'].splitlines()) > 30)

    def test_screen(self):
        try:
            # Launch some screens
            assert_equal(len(screen_launch(u'my_1st_screen', u'top', fail=False)[u'stderr']), 0)
            assert_equal(len(screen_launch(u'my_2nd_screen', u'top', fail=False)[u'stderr']), 0)
            assert_equal(len(screen_launch(u'my_2nd_screen', u'top', fail=False)[u'stderr']), 0)
            # List the launched screen sessions
            screens = screen_list(name=u'my_1st_screen')
            assert(len(screens) >= 1 and screens[0].endswith(u'my_1st_screen'))
            screens = screen_list(name=u'my_2nd_screen')
            assert(len(screens) >= 1 and screens[0].endswith(u'my_2nd_screen'))
        finally:
            # Cleanup
            kill_log = mock_cmd()
            screen_kill(name=u'my_1st_screen', log=kill_log)
            screen_kill(name=u'my_2nd_screen', log=kill_log)
            #raise NotImplementedError(kill_log.call_args_list)
            validate_list(kill_log.call_args_list, [
                r"call\(u*\"Execute \[u*'screen', u*'-ls', u*'my_1st_screen'\]\"\)",
                r"call\(u*\"Execute \[u*'screen', u*'-S', u*'\d+\.my_1st_screen', u*'-X', u*'quit'\]\"\)",
                r"call\(u*\"Execute \[u*'screen', u*'-ls', u*'my_2nd_screen'\]\"\)",
                r"call\(u*\"Execute \[u*'screen', u*'-S', u*'\d+\.my_2nd_screen', u*'-X', u*'quit'\]\"\)",
                r"call\(u*\"Execute \[u*'screen', u*'-S', u*'\d+\.my_2nd_screen', u*'-X', u*'quit'\]\"\)"])
