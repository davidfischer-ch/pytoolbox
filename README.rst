.. image:: https://badge.waffle.io/davidfischer-ch/pytoolbox.png?label=ready&title=Ready 
 :target: https://waffle.io/davidfischer-ch/pytoolbox
 :alt: 'Stories in Ready'
=========
pytoolbox
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

This library supports Python 2.7, 3.3, 3.4, 3.5, 3.6 and PyPy.
And try to support 2.6 and 3.2, see Travis CI build matrix.

------------------------------------
What the release number stands for ?
------------------------------------

I do my best to follow this interesting recommendation : `Semantic Versioning 2.0.0 <http://semver.org/>`_

--------------------------------
How to install it (Python 2.7) ?
--------------------------------

Install some packages that are not handled by pip::

    sudo apt-get install gir1.2-gexiv2-0.10 libexiv2-dev liblzma-dev libxml2-dev libxslt-dev libyaml-dev libz-dev
    sudo apt-get install ffmpeg git-core python-dev python-gi python-pip screen

Make sure that pip is up-to-date (PIPception)::

    sudo pip-2.7 install --upgrade pip

Then, you only need to run ``setup.py``::

    python2 setup.py test
    sudo python2 setup.py install

--------------------------------
How to install it (Python 3.5) ?
--------------------------------

Install some packages that are not handled by pip::

    sudo apt-get install gir1.2-gexiv2-0.10 libexiv2-dev liblzma-dev libxml2-dev libxslt-dev libyaml-dev libz-dev
    sudo apt-get install ffmpeg git-core python3-dev python3-gi python3-pip screen

Make sure that pip is up-to-date (PIPception)::

    sudo pip-3.5 install --upgrade pip

Then, you only need to run ``setup.py``::

    python3 setup.py test
    sudo python3 setup.py install

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
      ...
      --extra-all                          Install dependencies for all features.
      --extra-atlassian                    Install dependencies for the feature atlassian.
      --extra-django                       Install dependencies for the feature django.
      --extra-django-filter                Install dependencies for the feature django_filter.
      --extra-django-formtools             Install dependencies for the feature django_formtools.
      --extra-flask                        Install dependencies for the feature flask.
      --extra-mongo                        Install dependencies for the feature mongo.
      --extra-rest-framework               Install dependencies for the feature rest_framework.
      --extra-selenium                     Install dependencies for the feature selenium.
      --extra-smpte2022                    Install dependencies for the feature smpte2022.
      --extra-voluptuous                   Install dependencies for the feature voluptuous.

    usage: setup.py [global_opts] cmd1 [cmd1_opts] [cmd2 [cmd2_opts] ...]
       or: setup.py --help [cmd1 cmd2 ...]
       or: setup.py --help-commands
       or: setup.py cmd --help


    sudo python setup.py install --extra-smpte2022

Another way to do this, with ``pip``::

    sudo pip install -e .[django,flask,mongo,smpte2022] --use-mirrors

-----------------------
How to check coverage ?
-----------------------

::

    python setup.py test
    xdg-open tests/cover/index.html

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

    python setup.py docs
    xdg-open docs/build/html/index.html

-------------------------------------------------
How to add it to dependencies of my own project ?
-------------------------------------------------

Here is an example ``setup.py`` for a project called *my-cool-project*::

	from setuptools import setup

	setup(name='my-cool-project',
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

2014 - David Fischer
