#!/usr/bin/env python
# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2014 David Fischer. All rights reserved.
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

import shutil, sys
from pytoolbox.encoding import configure_unicode
from pytoolbox.subprocess import cmd
from pytoolbox.filesystem import from_template

configure_unicode()

# Detect modules, thanks to find !
modules = sorted(m.replace('.py', '').replace('./', '').replace('/', '.')
                 for m in cmd('find . -type f -name "*.py"', cwd='../pytoolbox', shell=True)['stdout'].split()
                 if m.endswith('.py') and not '__init__' in m)

print('Detected modules are: {0}'.format(modules))

api_toc = ''
for module in modules:
    if 'django' in module or 'crypto' in module:
        continue  # FIXME temporary hack, see issue #6
    module = 'pytoolbox.{0}'.format(module)
    title = module.replace('.', ' > ')
    api_toc += '    {0}\n'.format(module)
    from_template('templates/module.rst.template', 'source/{0}.rst'.format(module),
                  {'module': module, 'title': title, 'equals': '='*len(title)})

from_template('templates/api.rst.template', 'source/api.rst', {'api_toc': api_toc})
shutil.rmtree('build/html', ignore_errors=True)
result = cmd('make html', fail=False)

print('\nOutputs\n=======\n')
print(result['stdout'])
print('\nErrors\n======\n')
print(result['stderr'])

sys.exit(0 if not result['stderr'] else 1)
