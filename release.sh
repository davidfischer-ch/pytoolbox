#!/usr/bin/env bash

#**********************************************************************************************************************#
#                                       PYUTILS - TOOLBOX FOR PYTHON SCRIPTS
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

sudo python2 setup.py test || warning 'Python 2 unit-test of pytoolbox failed'
sudo python3 setup.py test || warning 'Python 3 unit-test of pytoolbox failed'
cd doc && sudo python2 update.py || warning 'Sphinx is not fully happy with our docstrings'
cd ..
version=$(cat setup.py | grep 'version=' | cut -d'=' -f2 | sed "s:',*::g")
echo "Release version $version, press enter to continue ..."
read a
git push || error 'Unable to push to GitHub' 1
git tag "$version" && git push origin "$version" || error 'Unable to add release tag' 2
sudo python2 setup.py register && sudo python2 setup.py sdist upload
