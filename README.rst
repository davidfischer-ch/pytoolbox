pyutils
=======

Some Python utility functions.

This module is a Toolbox for Python scripts.

How to install it ?
-------------------

You only need to run setup.py::

    sudo python setup.py install

How to use it ?
---------------

Here is an example ``hello.py`` using the cmd function provided by pyutils::

    from pyutils import cmd

    cmd('echo Hello World!')

How to add it to dependencies of my own project ?
-------------------------------------------------

Here is an example setup.py of a project called my-cool-project::

	from setuptools import setup

	setup(name='my-cool-project',
		  version='0.8',
		  author='Firstname Lastname',
		  author_email='author@something.com',
		  install_requires=['...', 'pyutils', '...'],
		  dependency_links=['https://github.com/davidfischer-ch/pyutils/tarball/master#egg=pyutils-1.0'],
		  tests_require=['nose'],
		  license='GPLv3',
		  url='https://github.com/nickname/my-cool-project',
		  packages=['my_cool_project'])

2013 - David Fischer
