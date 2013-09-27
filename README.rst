pyutils
=======

.. image:: https://secure.travis-ci.org/davidfischer-ch/pyutils.png
	:target: http://travis-ci.org/davidfischer-ch/pyutils

Afraid of red status ? Please click on the link, sometimes this is not my fault ;-)

Some Python utility functions.

This module is a Toolbox for Python scripts.

What the release number stands for ?
------------------------------------

I do my best to follow this interesting recommendation : `Semantic Versioning 2.0.0 <http://semver.org/>`_

How to install it (Python 2.7) ?
--------------------------------

Install some packages that are not handled by pip::

    sudo apt-get install ffmpeg git-core libyaml-dev libxml2-dev libxslt-dev libz-dev python-dev python-pip screen

Make sure that pip is up-to-date (PIPception)::

    sudo pip-2.7 install --upgrade pip

Then, you only need to run ``setup.py``::

    python2 setup.py test
    sudo python2 setup.py install

How to install it (Python 3.3) ?
--------------------------------

Install some packages that are not handled by pip::

    sudo apt-get install ffmpeg git-core libyaml-dev libxml2-dev libxslt-dev libz-dev python3-dev python3-pip screen

Make sure that pip is up-to-date (PIPception)::

    sudo pip-3.3 install --upgrade pip

Then, you only need to run ``setup.py``::

    python3 setup.py test
    sudo python3 setup.py install

How to check coverage ?
-----------------------

::

    python setup.py test
    xdg-open tests/cover/index.html

How to use it ?
---------------

Here is an example ``hello.py`` using the cmd function provided by ``pyutils``::

    from pyutils.py_subprocess import cmd

    print(cmd('echo Hello World!')['stdout'])

How to add it to dependencies of my own project ?
-------------------------------------------------

Here is an example ``setup.py`` for a project called *my-cool-project*::

	from setuptools import setup

	setup(name='my-cool-project',
		  version='0.8',
		  author='Firstname Lastname',
		  author_email='author@something.com',
		  install_requires=['...', 'pyutils', '...'],
                  dependency_links=['git+https://github.com/davidfischer-ch/pyutils.git@v4.8.7-beta#egg=pyutils'],
		  tests_require=['nose'],
		  license='GPLv3',
		  url='https://github.com/nickname/my-cool-project',
		  packages=['my_cool_project'])

You also need to install ``git-core``, but it is probably already the case, at least on your development computer ;-)

2013 - David Fischer
