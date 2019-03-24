=========
changelog
=========

-------
v13.1.3
-------

Fix and enhancements
====================

* Module mutlimedia.exif: Make classes swappable + importable from exif module.
* Module smpte2022: Fixed wraparound sequence number calculations for RTP and FEC.

Thanks to @TobbeEdgeware!

-------
v13.1.1
-------

Minor compatibility breaks
==========================

* Function serialization.object_to_dict: Rely almost only on schema to produce output structure (hint: use list in schema)

Fix and enhancements
====================

* Function collections.swap_dict_of_values: Implement simple key-value swap.

-------
v13.0.4
-------

Fix and enhancements
====================

* Function aws.s3.remove_objects: Add callback argument to make it more flexible.
* Function multimedia.image.remove_transparency: Enhance code (remove force_rgb arg from 13.0.2).
* Function serialization.object_to_dict: Add iterable_callback to customize container type of iterables.

-------
v13.0.0
-------

Compatibility breaks
====================

* Remove fake bson ObjectId (private module) when library not available.
* Function filesystem.find_recursive is now matching patterns against the whole path.
* Function aws.s3.list_objects: Handle multiple patterns like filesystem.find_recursive.
* Function aws.s3.remove_objects: Handle multiple patterns like filesystem.find_recursive.

Features
========

* Add function filesystem.to_user_id
* Add function filesystem.to_group_id
* Add function regex.from_path_patterns

Fix and enhancements
====================

* Replace relative imports of len(.) > 1 by absolute imports

-------
v12.2.3
-------

Features
========

* Add module aws.s3

-------
v12.1.2
-------

Compatibility breaks
====================

* Remove object_to_dict and object_to_dictV2
* Rename object_to_dictV3 to object_to_dict

Fix and enhancements
====================

* Move AI data to S3 (own account).
* Function serialization.object_to_dict: Also authorize to tweak obj (not only schema).
* Function serialization.object_to_dict: Also add depth information.
* Function serialization.to_file: Fix to_file ot using makedirs properly

--------
v11.10.0
--------

Fix and enhancements
====================

* Fix PEP-8 issue
* Class django.models.fields.base.MoneyField: Make decimal_places tweakable

Features
========

* Add class django.models.fields.mixins.LowercaseMixin
* Add function serialization.object_to_dictV3

-------
v11.9.1
-------

Fix and enhancements
====================

* Set line size to 100 chars and cleanup code
* Fix Travis build (remove django modules when testing)
* Always install pillow when installing with -e imaging
* Update README to reflect newer options

* Class multimedia.exif.brand.Brand: Add more brands
* Class multimedia.exif.image.Orientation: Use standard Enum, or object if not available

Features
========

* Add module ai

-------
v11.8.6
-------

Fixes and enhancements
======================

* Add functions multimedia.image.PIL.{apply,get}_orientation
* Add constant ORIENTATION_TO_ROTATION to multimedia.exif.image.Image
* Make function multimedia.image.PIL.apply_orientation more generic
* Make function multimedia.image.PIL.apply_orientation defaulting to nothing if orientation is crazy
* Make function multimedia.image.PIL.get_orientation more robust
* Class exceptions.MessageMixin: Fix pickle recursion error

Features
========

* Add module multimedia.image.PIL
* Add function types.merge_base_attribute

-------
v11.7.6
-------

Minor compatibility breaks
==========================

* Remove jinja2 from packages installed by default

Fixes and enhancements
======================

* Support more Python versions (3.5, 3.6)
* Function filesystem.makedirs: Add parent argument
* Module logging: Update logging color scheme + make it overridable
* Module django.templatetags:
    - Implement TEMPLATE_STRING_IF_INVALID for Django >= 1.8
    - Implement include_is_allowed for Django >= 1.10
* Class multimedia.exif.Metadata: Can also read EXIF metadata from buffer
* Function argparse.password: Add it

-------
v11.7.1
-------

Minor compatibility breaks
==========================

* Remove unnecessary dependencies + put some as extra

Fixes and enhancements
======================

* Module filesystem: Add walk_kwargs to some functions
* Function logging.setup_logging: make possible to setup an instance of logger

-------
v11.6.4
-------

Fixes and enhancements
======================

* Module argparse: Set columns to a value or auto-detected
* Module exif: Fix orientation is not value from Orientation
* Module smpte2022: Various fixes by @AbdulTheProgrammer
* Enhance function logging.setup_logging:
    - Add optional colorized mode
    - Always setup log level and return logger
* Enhance module multimedia.exif:
    - Add optional orientation override
    - Add rotation property based on orientation
    - Add rewrite method to fix issues with exif tags
    - Allow to specify gexiv2 version
* Use iteritems because its still a Python 2 (and 3) library

-------
v11.6.0
-------

Fixes and enhancements
======================

* Add method get_frames_md5_checksum to FFmpeg class
* Update exif brands

Features
========

* Support Python 3.6
* Add function itertools.chunk

-------
v11.5.4
-------

Fixes and enhancements
======================

* Fix syntax error in multimedia.exif.lens at line 22
* Prevent AppRegistryNotReady when importing django.models.utils
* Add {pre,post}_func arguments to filesystem.from_template
* Function filesystem.from_template: Make destination optional + allow to set template to content

Features
========

* Add function crypto.get_password_generator

-------
v11.5.0
-------

Fixes and enhancements
======================

* Improve code quality
* Remove try_ prefix from filesystem functions (retro compat: try_ functions still defined)

-------
v11.4.3
-------

Features
========

* Add constant encoding.integer_types
* Add function subprocess.su
* Add function types.get_arguments_names

Fixes and enhancements
======================

* Add bare argument to subprocess.git_clone_or_pull

-------
v11.4.0
-------

Features
========

* Add module linux
* Add module setuptools

-------
v11.2.0
-------

Features
========

* Add classes types.Echo{Object,Dict}
* Add classes argparse.Help{ArgumentParser,Formatter}

Fixes and enhancements
======================

* Add docstrings and fix doctests
* Fix django.forms.utils.get_instance
* Update FromPrivateKeyMixin to fix call to fail with recent DRF

-------
v11.1.0
-------

Minor compatibility breaks
==========================

* Update git_clone_or_pull to full clone by default

Features
========

* Add module network.url
* Add mixin django.forms.mixins.CreatedByMixin
* Add mixin django.forms.mixins.StaffOnlyFieldsMixin

Fixes and enhancements
======================

* Add/fix docstrings and unit-tests
* Use xrange and iter{items,keys,values} under Python 2
* Replace nose.tools by pytoolbox.unittest.asserts
* Make RequestMixin more transparent
* network.http.download_ext: Pass kwargs to iter_download_to_file
* django.views.mixins.AddRequestToFormKwargsMixin: Check form "handles" request as kwarg based on its class

-------
v11.0.0
-------

Compatibility breaks
====================

* Remove ming module to cleanup build
* Remove django.models.mixins.PublishedMixin (not generic enough neither powerful enough)

Minor compatibility breaks
==========================

* Prefer path over filename (arguments convention)
* Replace MapUniqueTogetherMixin + MapUniqueTogetherIntegrityErrorToValidationErrorMixin by BetterUniquenessErrorsMixin.
* Move CancellableDeleteView to django.views.base

Features
========

* Generate documentation and publish on readthedocs.org
* Add mixin django.models.mixins.BetterUniquenessErrorsMixin

Fixes and enhancements
======================

* Add/fix docstrings
* Update modules headers
* Make django.views.mixins.ValidationErrorsMixin more "generic"
* Too many to be listed here, https://github.com/davidfischer-ch/pytoolbox/compare/10.4.0...11.0.0

-------
v10.4.0
-------

Features
========

* Add module django.models.metaclass
* Add module django.views.utils
* Add module enum
* Add modules in multimedia.exif:
    - brand
    - camera
    - equipement
    - image
    - lens
    - photo
    - tag
* Add module rest_framework.metadata.mixins
* Add mixin django.models.mixins.PublicMetaMixin
* Add decorator decorators.cached_property
* Add decorator decorators.hybridmethod
* Add functions in django.models.utils:
    - get_related_manager
    - get_related_model
    - try_get_field
* Add function types.get_properties

Fixes and enhancements
======================

* Handle 24h+ hour format in datetime.str_to_datetime
* Module django.forms.utils imports from django.forms.utils module
* Fix ReloadMixin popping update_fields!
* Refactor class multimedia.exif.metadata.Metadata (use newest classes)
* Split module multimedia.ffmpeg
* Fix ffmpeg mock class

-------
v10.3.0
-------

Compatibility breaks
====================

* Remove module rest_framework.v2
* Refactor (optimize) unittest.FilterByTagsMixin

Minor compatibility breaks
==========================

* Rename module exception to exceptions
* Rename module rest_framework.v3 to rest_framework
* Rename some attributes of multimedia.ffmpeg classes

Features
========

* Add many modules:
    - atlassian
    - itertools
    - module (yes!)
    - selenium
    - signals
    - states
    - string
    - voluptuous
* Add functions:
* Add class argparse.Range
* Add function argparse.multiple
* Add function collections.{merge_dicts, swap_dict_of_values}
* Add decorator decorators.run_once
* Add modules and mixins in django* module
* Add value encoding.binary_type
* Add function humanize.naturalfrequency
* Add function types.isiterable
* Add classes types.{DummyObject,MissingType}
* Add object types.Missing instance of MissingType
* Add mixins unittest.{InMixin,InspectMixin}
* Add class unittest.Asserts
* Add object unittest.asserts

Fixes and enhancements
======================

* Countless fixes and enhancements
* Follow os.path import best practices
* Make multimedia.ffmpeg private functions public

-------
v10.2.0
-------

Compatibility breaks
====================

* Add EncodeStatistics and refactor FFmpeg.encode()

Minor compatibility breaks
==========================

* Merge django.template tags & filters into 1 file
* Split FFmpeg class to FFmpeg + FFprobe classes

Features
========

* Add module django.exceptions
* Add static_abspath Django template tag
* Add class django.forms.mixins.EnctypeMixin
* Add class django.models.mixins.AlwaysUpdateFieldsMixin
* Add class django.models.mixins.AutoForceInsertMixin
* Add class django.models.mixins.AutoUpdateFieldsMixin
* Add class django.models.mixins.MapUniqueTogetherIntegrityErrorToValidationErrorMixin
* Add class django.models.mixins.RelatedModelMixin
* Add class django.models.mixins.UpdatePreconditionsMixin
* Add class django.storage.ExpressTemporaryFileMixin
* Add class django.test.mixins.FormWizardMixin
* Add class django.views.mixins.InitialMixin
* Add class logging.ColorizeFilter
* Add function collections.flatten_dict
* Add function datetime.multiply_time

Fixes and enhancements
======================

* Avoid hardcoding \n
* Module console: Write to given stream
* Module datetime: Make API more consistent
* Module multimedia.ffmpeg:
    - Split FFmpeg class in FFmpeg and FFprobe
    - Add EncodeState & EncodeStatistics classes
    - Do some analysis before launching ffmpeg subprocess
    - Fix progress if sub-clipping
    - Improve handling of media argument
    - Miscellaneous improvements
* Module subprocess: Import Popen from psutil if available
* Refactor function django.signals.create_site

-------
v10.0.0
-------

Compatibility breaks
====================

* Method multimedia.ffmpeg.FFmpeg.encode always yields at start

Features
========

* Add some mixins in rest_framework.v*.views.mixins

Fixes and enhancements
======================

* Add class multimedia.ffmpeg.EncodingState

------
v9.7.2
------

Minor compatibility breaks
==========================

* Function filesystem.get_bytes returns a generator
* Rename all functions with _to_ instead of 2 (e.g. str2time -> str_to_time)
* Rename some methods of the class ffmpeg.FFmpeg
* Change signature of console module functions

Features
========

* Add module comparison
* Add module regex
* Add module types
* Add class filesystem.TempStorage
* Add function exception.get_exception_with_traceback
* Add function humanize.natural_int_key
* Add function console.progress_bar

Fixes and enhancements
======================

* Add *streams* methods to ffmpeg.FFmpeg
* Improve ffmpeg module (add Media class for inputs/outputs)
* Improve network.http.download_ext (Can download in chunks + progress callback)
* Improve filesystem.get_bytes + crypto.* to read a file in chunks (if chunk_size is set)

------
v9.4.2
------

Features
========

* Add module humanize
* Add module django.models.query.mixins
* Add module django.test.runner.mixins

Fixes and enhancements
======================

* Add __all__ to make the API explicit
* Add method get_media_framerate to FFmpeg class
* Add module private (with _parse_kwargs_string)
* network module: Cleaner usage of string.format()
* Refactor module humanize + add naturalfilesize
* Improve humanize functions to handle [0-1] range + big numbers

-----------
v9.3.0-beta
-----------

Compatibility breaks
====================

* Refactor multimedia modules
* Rename module django.templatetags.pytoolbox_tags to _filters

Minor compatibility breaks
==========================

* Rename django.forms -> django.forms.mixins
* Rename django.views -> django.views.mixins

Features
========

* Add module django.templatetags.pytoolbox_tags
* Add module multimedia.exif
* Add some django mixins

Fixes and enhancements
======================

* Fix unicode handling
* Function datetime.total_seconds now accept instance of timedelta
* Function filesystem.from_template can now use jinja2 to generate the content
* timedelta & to_filesize Django template filters now handle empty string input
* Add argument create_out_directory to method multimedia.ffmpeg.FFmpeg.encode
* Fix multimedia.ffmpeg.FFmpeg.encode: Create output directory before the subprocess
* Improve multimedia.ffmpeg.FFmpeg.encode: Handle process missing + simplify mocking

-----------
v8.6.1-beta
-----------

Fixes and enhancements
======================

* Add function multimedia.ffmpeg.get_subprocess

-----------
v8.6.0-beta
-----------

Minor compatibility breaks
==========================

* Rename module django.models -> django.models.mixins

Features
========

* Add module django.models.fields
* Add class validation.CleanAttributesMixin
* Add class validation.StrongTypedMixin
* Add class django.forms.RequestMixin
* Add class django.views.AddRequestToFormKwargsMixin
* Add class django.views.LoggedCookieMixin
* Add class unittest.AwareTearDownMixin
* Add function subprocess.git_add_submodule
* Add function network.http.download_ext
* Add function datetime.parts_to_time

Fixes and enhancements
======================

* Add some classes in module exception
* Add module django.urls with utility regular expressions
* Improve crypto.githash to handle reading data from a file
* Fix SaveInstanceFilesMixin (use .pk instead of .id)
* Improve datetime.str2time to handle microseconds
* Improve filesystem.try_remove to handle directories (when recursive=True)
* Improve multimedia.ffprobe.get_media_duration (return None in case of error)
* StrongTypedMixin: Allow setting arg to the default value (if set)
* Split HelpTextToPlaceholderMixin logic to allow modify behavior by inheritance
* Fix multimedia.ffmpeg.encode (convert default_in_duration to time)
* Fix multimedia.ffmpeg.encode (may return None - out_duration)
* Fix multimedia.ffmpeg.encode (skip broken out duration)
* Improve multimedia.ffprobe.get_media_duration to handle media info dict

-----------
v8.0.0-beta
-----------

Compatibility breaks
====================

* Move ffmpeg and x264 modules into multimedia
* Replace unreliable ffmpeg.get_media_* functions by multimedia.ffprobe.get_media_*

Features
========

* Add module multimedia.ffprobe
* Add function datetime.str2time

------------
v7.1.17-beta
------------

Compatibility breaks
====================

* Store command line arguments in args attribute, do not update __dict__ of the instance.

Features
========

* Add module argparse

Fixes and enhancements
======================

* Add function argparse.is_file
* Add cleanup argument to juju.boostrap
* Add docstring to function juju.ensure_num_units
* Add get_unit_public_address + properties methods to class juju.Environment (thanks @smarter)
* Add args and namespace kwargs to juju.DeploymentScenario __init__ to allow bypassing sys.arv
* Fix various bugs of juju module + various updates according to juju 1.18
* Fix subprocess.rsync
* Fix crypto.githash
* Fix handling of juju bootstrap error message in Python 3
* Default to something if key is missing in stats (x264.encode)
* Use sudo with juju status (to work around https://bugs.launchpad.net/juju-core/+bug/1237259)
* Add timeout to valid_uri

-----------
v6.6.0-beta
-----------

Compatibility breaks
====================

* Improve errors and time-outs handling in juju module (for the best)
* Move socket & twisted fec generators to pytoolbox_bin

Minor compatibility breaks
==========================

* Remove deprecated flask.get_request_data (replaced by network.http.get_requests_data)
* SmartJSONEncoderV2 now filter the class attributes
* Fix SmartJSONEncoderV2!

Features
========

* Add module decorators
* Add module django.utils
* Add module x264
* Add function datetime.secs_to_time
* Add function datetime.time_ratio
* Add function ffmpeg.get_media_resolution
* Add function mongo.mongo_do
* Add function network.http.download
* Add function subprocess.git_clone_or_pull

Fixes and enhancements
======================

* Fix test_ensure_num_units, str2datetime
* Fix computation of FecReceiver.lostogram
* Fix usage of time_ratio by ffmpeg and x264 modules
* Use renamed IP class (previously IPAddress) fallback import to IPAddress
* Accept None to leave owner or group unchanged (filesystem.chown)
* Set default time-outs to None and update juju module (fixes)
* Add some arguments to recursive_copy and rsync
* Append sudo to juju bootstrap
* Add juju.Environment.wait_unit
* Improve ffmpeg module

-----------
v5.6.3-beta
-----------

Fixes and enhancements
======================

* Add timeout argument to cmd()
* Remove symlink first, to avoid boring exceptions
* Add timeout to juju status !

-----------
v5.6.0-beta
-----------

Features
========

* Add function validation.valid_int()

Fixes and enhancements
======================

* Add constants to juju module
* Juju bootstrap will print time as int
* Add makedirs argument to some methods of the objects of serialization
* Add user argument to function subprocess.cmd
* Add path argument to subprocess.make
* Add extra_args (list) to function subprocess.rsync

* Fix juju, serialization, subprocess modules, update tests
* Function subprocess.cmd : Handle logging.Logger as log, improve docstring, add retry loop
* Upgrade relation_ methods

------------
v5.5.0-beta
------------

Minor compatibility breaks
==========================

* Move all django template tags into module pytooblox_tags
* Move juju functions to the Environment class

Features
========

* Add console.choice() (by kyouko-taiga)
* Add function serialization.to_file and use it to improve PickeableObject and JsoneableObject write methods.

Fixes and enhancements
======================

* Add missing MANIFEST.in
* Add new django-related modules
* Add some django mixins + template tags
* Make class django.models.GoogleMapsMixin more generic
* Add cli_output argument to subprocess.cmd
* Add size_only argument to subprocess.rsync
* Do not add hashlib to requirements if already part of the stdlib
* Fix headers + rest markup + update title
* Enhance function ffmpeg.encode
* Call log more often

------------
v5.4.19-beta
------------

Deprecated
==========

* flask.get_request_data replaced by network.http.get_request_data

Minor compatibility breaks
==========================

* Split django module into submodules
* Rename SmartModel to AbsoluteUrlMixin

Features
========

* Embed smpte2022lib
* Add entry points (socket-fec-generator + twisted-fec-generator)
* Add commit and release scripts to make it more securely (run tests before, check sphinx ...)
* Add module network.http and classes juju.SimulatedUnit(s)
* Add module django.templatetags with getattribute function
* Add class django.models.SaveInstanceFilesMixin
* Add function django.forms.update_widget_attributes

Fixes and enhancements
======================

* Lighter list of dependencies
* Add --extra-... flags to install dependencies for the extra features/modules.
* Filter packages to avoid installing tests module !
* Fix setup.py to avoid removing tests from packages list if it did not exist.
* Add kwargs to serialization.object2json -> json.dumps
* map_marker : Convert to unicode sooner (to handle special field class)
* django.forms.SmartModelForm : Attributes & replacement class applied depending of the form field's class
* Add fill option to collections.pygal_deque.list()
* Replace range by xrange, values by itervalues, ...
* Handle datetime.date class (function datetime.dateime2epoch)
* Add suffix parameter to AbsoluteUrlMixin.get_absolute_url
* Ensure import from future of great things
* Fix docstrings

Example usage::

    sudo python setup.py install --help
    sudo python setup.py install --extra-flask

-----------
v5.0.0-beta
-----------

Compatibility breaks
====================

* Remove py_ prefix of all modules & paths
* Change license (GNU GPLv3 -> EUPL 1.1)

Features
========

* Add module mongo

Fixes and enhancements
======================

* Use absolute imports
* Update classifiers
* Update README.rst

-----------
v4.8.7-beta
-----------

Minor compatibility breaks
==========================

* Rename duration2secs -> total_seconds
* Rename get_request_json -> get_request_data

Features
========

* Python 3 support
* Add module py_collections
* Add module py_django
* Add function json_response2dict
* Add function make
* Add function ssh
* Greatly improve module py_juju
* Greatly improve module py_serialization

Fixes and enhancements
======================

* Update README.rst
* Update function get_request_data
* Update function map_exceptions
* Update function runtests
* Update setup.py

------------
v4.0.0-beta
------------

Compatibility breaks
====================

* Greatly improve module py_serialization

Features
========

* Greatly improve module py_juju
* Add class TimeoutError
* Add function print_error

Fixes and enhancements
======================

* Fix setup.py
* Update cmd
* Update rsync

------------
v3.10.7-beta
------------

Compatibility breaks
====================

* Rename module py_mock -> py_unittest
* Remove function unicode_csv_reader

Features
========

* Add module py_console
* Add module py_unicode
* Add module and function runtests
* Add class JsoneableObject
* Add function assert_raises_item
* Add function valid_uri
* Add function validate_list
* Greatly improve module py_juju
* Greatly improve setup and unit-testing

Fixes and enhancements
======================

* Fix shebangs
* Handle unicode
* Use new string formatting
* Update function map_exceptions
* Add kwargs to functions of module py_subprocess
