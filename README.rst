=========
Pytoolbox
=========

.. image:: https://badge.fury.io/py/pytoolbox.png
   :target: http://badge.fury.io/py/pytoolbox

.. image:: https://secure.travis-ci.org/davidfischer-ch/pytoolbox.png
   :target: http://travis-ci.org/davidfischer-ch/pytoolbox

.. image:: https://coveralls.io/repos/davidfischer-ch/pytoolbox/badge.png
   :target: https://coveralls.io/r/davidfischer-ch/pytoolbox

.. image:: https://landscape.io/github/davidfischer-ch/pytoolbox/master/landscape.png
   :target: https://landscape.io/github/davidfischer-ch/pytoolbox/master

.. image:: https://badge.waffle.io/davidfischer-ch/pytoolbox.png?label=ready&title=Ready
   :target: https://waffle.io/davidfischer-ch/pytoolbox
   :alt: 'Stories in Ready'

Afraid of red status ? Please click on the link, sometimes this is not my fault ;-)

This module is a Toolbox for Python scripts.

Documentation: https://pytoolbox.readthedocs.org

Repository: https://github.com/davidfischer-ch/pytoolbox

This library supports Python 3.6, 3.7, 3.8... and PyPy 3.6.

------------------------------------
What the release number stands for ?
------------------------------------

I do my best to follow this interesting recommendation : `Semantic Versioning 2.0.0 <http://semver.org/>`_

-------------------
How to install it ?
-------------------

Install some packages that are not handled by pip::

    sudo apt-get install gir1.2-gexiv2-0.10 libexiv2-dev liblzma-dev libxml2-dev libxslt-dev libyaml-dev libz-dev
    sudo apt-get install ffmpeg git-core python3-dev python3-gi python3-pip screen

Make sure that pip is up-to-date (PIPception)::

    source /some/python3/venv
    pip install --upgrade pip

Then, you only need to run ``setup.py``::

    source /some/python3/venv
    python setup.py test
    python setup.py install

--------------------------------
How to enable features/modules ?
--------------------------------

Example::

    python setup.py install --help

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
      --prefix                             installation prefix
      --exec-prefix                        (Unix only) prefix for platform-specific files
      --home                               (Unix only) home directory to install under
      --install-base                       base installation directory (instead of --prefix or --home)
      ...
      --extra-all                          Install dependencies for all features.
      --extra-atlassian                    Install dependencies for the feature atlassian.
      --extra-aws                          Install dependencies for the feature aws.
      --extra-django                       Install dependencies for the feature django.
      --extra-django-filter                Install dependencies for the feature django_filter.
      --extra-django-formtools             Install dependencies for the feature django_formtools.
      --extra-flask                        Install dependencies for the feature flask.
      --extra-imaging                      Install dependencies for the feature imaging.
      --extra-jinja2                       Install dependencies for the feature jinja2.
      --extra-logging                      Install dependencies for the feature logging.
      --extra-mongo                        Install dependencies for the feature mongo.
      --extra-network                      Install dependencies for the feature network.
      --extra-pandas                       Install dependencies for the feature pandas.
      --extra-rest-framework               Install dependencies for the feature rest_framework.
      --extra-selenium                     Install dependencies for the feature selenium.
      --extra-smpte2022                    Install dependencies for the feature smpte2022.
      --extra-unittest                     Install dependencies for the feature unittest.
      --extra-vision                       Install dependencies for the feature vision.
      --extra-voluptuous                   Install dependencies for the feature voluptuous.

    usage: setup.py [global_opts] cmd1 [cmd1_opts] [cmd2 [cmd2_opts] ...]
       or: setup.py --help [cmd1 cmd2 ...]
       or: setup.py --help-commands
       or: setup.py cmd --help


    python setup.py install --extra-smpte2022

Another way to do this, with ``pip``::

    pip install -e .[django,flask,mongo,smpte2022] --use-mirrors

-----------------------
How to check coverage ?
-----------------------

::

    source /some/python3/venv
    python setup.py test
    xdg-open tests/cover/index.html

Remarks:

* All Django related modules are excluded from tests!
* However I am using them with Django 1.8 up to 3.0.5.

---------------
How to use it ?
---------------

Here is an example ``hello.py`` using the cmd function provided by ``pytoolbox``::

    from pytoolbox.subprocess import cmd

    print(cmd('echo Hello World!')['stdout'])

-------------------------------
How to generate documentation ?
-------------------------------

The documentation is generated by `Sphinx <http://sphinx-doc.org/ext/autodoc.html>`_.
In fact most of this documentation is extracted from the docstrings of the code.

Here is the procedure::

    source /some/python3/venv
    pip install sphinx
    python setup.py docs
    xdg-open docs/build/html/index.html

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
		  install_requires=['...', 'pytoolbox', '...'],
		  tests_require=['nose'],
		  license='GPLv3',
		  url='https://github.com/nickname/my-cool-project',
		  packages=['my_cool_project'])


See `pip vcs support <http://www.pip-installer.org/en/latest/logic.html#vcs-support>`_ to get further details about this.

You also need to install ``git-core``, but it is probably already the case, at least on your development computer ;-)

2014 - 2020 David Fischer
