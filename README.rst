=========
Pytoolbox
=========

.. image:: https://badge.fury.io/py/pytoolbox.png
   :target: http://badge.fury.io/py/pytoolbox

.. image:: https://github.com/davidfischer-ch/pytoolbox/actions/workflows/python-package.yml/badge.svg
   :target: https://github.com/davidfischer-ch/pytoolbox

.. image:: https://coveralls.io/repos/davidfischer-ch/pytoolbox/badge.png
   :target: https://coveralls.io/r/davidfischer-ch/pytoolbox

Afraid of red status ? Please click on the link, sometimes this is not my fault ;-)

This module is a Toolbox for Python scripts.

Documentation: https://pytoolbox.readthedocs.org

Repository: https://github.com/davidfischer-ch/pytoolbox

This library supports Python 3.11 and more recent.

------------------------------------
What the release number stands for ?
------------------------------------

I do my best to follow this interesting recommendation : `Semantic Versioning 2.0.0 <http://semver.org/>`_

-------------------
How to install it ?
-------------------

Install some packages that are not handled by pip::

    $ sudo apt install liblzma-dev libxml2-dev libxslt-dev libyaml-dev libz-dev
    $ sudo apt install ffmpeg git-core python3-dev python3-gi python3-pip screen

If planning to use the `imaging` extra, especially the `exif` classes, then you'll have to install::

    $ sudo apt install libcairo2 libcairo2-dev libexiv2-dev libgexiv2-dev libgirepository1.0-dev

The gir1.2-gexiv2-0.10 should also be installed, maybe its already the case.

You may find useful to read `PyGObject's documentation <https://pygobject.readthedocs.io/en/latest/getting_started.html>`_.

If planning to use the vision feature, then you have to install some requirements for dlib::

    $ sudo apt install build-essential cmake pkg-config

See https://learnopencv.com/install-dlib-on-ubuntu/ for an up-to-date procedure.

Make sure that pip is up-to-date (PIPception)::

    $ source /some/python3/venv/bin/active
    $ pip install --upgrade pip setuptools wheel

Then, you only need to run ``setup.py``::

    $ source /some/python3/venv/bin/activate
    $ pip install .

--------------------------------
How to enable features/modules ?
--------------------------------

Example::

    $ python setup.py install --help

    Common commands: (see '--help-commands' for more)

      setup.py build      will build the package underneath 'build/'
      setup.py install    will install the package

    Global options:
      --verbose (-v)  run verbosely (default)
      --quiet (-q)    run quietly (turns verbosity off)
      --dry-run (-n)  don't actually do anything
      --help (-h)     show detailed help message
      --no-user-cfg   ignore pydistutils.cfg in your home directory

    Options for 'WithExtra' command:
      ...
      --extra-all                          Install dependencies for All Modules.
      --extra-atlassian                    Install dependencies for Atlassian.
      --extra-aws                          Install dependencies for AWS.
      --extra-django                       Install dependencies for Django.
      --extra-django-filter                Install dependencies for Django Filter.
      --extra-django-formtools             Install dependencies for Django Form Tools.
      --extra-flask                        Install dependencies for Flask.
      --extra-imaging                      Install dependencies for Imaging.
      --extra-jinja2                       Install dependencies for Jinja2.
      --extra-network                      Install dependencies for Networking.
      --extra-pandas                       Install dependencies for Pandas.
      --extra-rest-framework               Install dependencies for Django REST Framework.
      --extra-selenium                     Install dependencies for Selenium.
      --extra-smpte2022                    Install dependencies for SMPTE-2022.
      --extra-unittest                     Install dependencies for Unit Test.
      --extra-vision                       Install dependencies for Vision.
      --extra-voluptuous                   Install dependencies for Voluptuous.
      --extra-doc                          Install dependencies for Pytoolbox Docs.
      --extra-test                         Install dependencies for Pytoolbox Tests.

    usage: setup.py [global_opts] cmd1 [cmd1_opts] [cmd2 [cmd2_opts] ...]
       or: setup.py --help [cmd1 cmd2 ...]
       or: setup.py --help-commands
       or: setup.py cmd --help


    $ python setup.py install --extra-smpte2022

Another way to do this, with ``pip``::

    $ pip install -e .[django,flask,mongo,smpte2022]

-----------------------
How to check coverage ?
-----------------------

::

    $ source /some/python3/venv/bin/activate
    $ pip install -e .[all,test]
    $ flake8 pytoolbox
    $ pytest
    $ xdg-open htmlcov/index.html

Remarks:

* All Django related modules are excluded from tests!
* However I am using them with Django 1.8 up to 3.1.0.

---------------
How to use it ?
---------------

Here is an example ``hello.py`` using the cmd function provided by ``pytoolbox``::

    $ from pytoolbox.subprocess import cmd
    $ print(cmd('echo Hello World!')['stdout'])

-------------------------------
How to generate documentation ?
-------------------------------

The documentation is generated by `Sphinx <http://sphinx-doc.org/ext/autodoc.html>`_.
In fact most of this documentation is extracted from the docstrings of the code.

Here is the procedure::

    $ source /some/python3/venv/bin/activate
    $ pip install -e .[docs]
    $ xdg-open docs/build/html/index.html

-------------------------------------------------
How to add it to dependencies of my own project ?
-------------------------------------------------

Here is an example ``setup.py`` for a project called *my-cool-project*::

	from setuptools import setup

	setup(
      name='my-cool-project',
		  version='0.8',
		  author='Firstname Lastname',
		  author_email='author@something.com',
		  install_requires=['...', 'pytoolbox>=14<15', '...'],
		  tests_require=['...', 'pytest', '...'],
		  license='GPLv3',
		  url='https://github.com/nickname/my-cool-project',
		  packages=['my_cool_project'])


See `pip vcs support <http://www.pip-installer.org/en/latest/logic.html#vcs-support>`_ to get further details about this.

You also need to install ``git-core``, but it is probably already the case, at least on your development computer ;-)

2014 - 2022 David Fischer
