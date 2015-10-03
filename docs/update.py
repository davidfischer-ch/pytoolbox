#!/usr/bin/env python
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

import os, shutil, sys

from pytoolbox.encoding import configure_unicode
from pytoolbox.subprocess import cmd
from pytoolbox.filesystem import find_recursive, from_template
from pytoolbox.string import to_lines

PACKAGE_DIRECTORY = os.path.join('..', 'pytoolbox')


def main():
    configure_unicode()

    # Cleanup previously generated restructured files
    for path in find_recursive('source', r'^pytoolbox.*\.rst$', unix_wildcards=False):
        os.remove(path)

    submodules = sorted(
        m.replace('.py', '').replace(PACKAGE_DIRECTORY, '').strip(os.path.sep).replace(os.path.sep, '.')
        for m in find_recursive(PACKAGE_DIRECTORY, r'[^_].*\.py$', unix_wildcards=False)
    )

    print('Detected modules are: {0}'.format(to_lines(submodules)))

    modules = []
    for submodule in submodules:
        if 'django' in submodule or 'crypto' in submodule:
            continue  # FIXME temporary hack, see issue #6
        module = 'pytoolbox.{0}'.format(submodule)
        title = module.replace('.', ' > ')
        modules.append(module)
        from_template(os.path.join('templates', 'module.rst.template'), os.path.join('source', module + '.rst'), {
            'module': module, 'title': title, 'equals': '='*len(title)
        })

    from_template(os.path.join('templates', 'api.rst.template'), os.path.join('source', 'api.rst'), {
        'api_toc': os.linesep.join('    ' + m for m in modules)
    })
    shutil.rmtree(os.path.join('build', 'html'), ignore_errors=True)
    result = cmd('make html', fail=False)

    print('{0}Outputs{0}======={0}{0}{1[stdout]}{0}{0}Errors{0}======{0}{0}{1[stderr]}'.format(os.linesep, result))

    sys.exit(1 if result['stderr'] else 0)

if __name__ == '__main__':
    main()
