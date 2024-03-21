#!/usr/bin/env bash

# **************************************************************************************************
#                              PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2018 David Fischer. All rights reserved.
#
# **************************************************************************************************
#
# This file is part of David Fischer's pytoolbox Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the
# EUPL v. 1.1 as provided by the European Commission. This project is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

warning()
{
    echo "[WARNING] $1" 1>&2
    echo 'press enter to continue or ctrl+c to exit ...'
    read a
}

error()
{
    echo "[ERROR] $1" 1>&2
    exit $2
}

version=$(cat 'pytoolbox/__init__.py' | grep '__version__ = ' | cut -d'=' -f2 | sed "s:'::g;s: ::g")
echo "Release version $version, press enter to continue ..."
read a

#git push || error 'Unable to push to GitHub' 1
#git tag "$version" && git push origin "$version" || error 'Unable to add release tag' 2

rm -rf dist/ 2>/dev/null
python3 setup.py sdist bdist_wheel || error 'Unable to build for Python 3' 4
twine upload dist/* --skip-existing || error 'Unable to upload to PyPI' 5
