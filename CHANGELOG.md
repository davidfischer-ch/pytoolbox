# Changelog

Roadmap ? Not so, but you can check this: https://github.com/davidfischer-ch/pytoolbox/issues

## v14.8.5 (2025-02-14)

Diff: https://github.com/davidfischer-ch/pytoolbox/compare/14.8.4...14.8.5

### Features

* Make `subprocess` Windows compatible (with some restrictions)

### Fix and enhancements

* Merge MRs from dependabot

## v14.8.4 (2024-11-09)

Diff: https://github.com/davidfischer-ch/pytoolbox/compare/14.8.3...14.8.4

### Features

* Module `multimedia.exif`: Rework it (better typing, None instead of 0, ...)
* Module `multimedia.exif`: Cover it with tests (still some more are welcome)
* Class `multimedia.exif.Metadata`: Convert path to string to fix issues with Gexiv2

### Fix and enhancements

* Integrate latest pylintrc
* Fix various linter issues

## v14.8.3 (2024-06-20)

Diff: https://github.com/davidfischer-ch/pytoolbox/compare/14.8.2...14.8.3

### Features

* Make `filesystem` Windows compatible (with some restrictions)

### Fix and enhancements

* Add `.flake8` configuration
* Merge MR from dependabot

## v14.8.2 (2024-04-03)

Diff: https://github.com/davidfischer-ch/pytoolbox/compare/14.8.1...14.8.2

### Features

* Add TypeAlias `git.RefKind` and use it
* Add function `logging.reset_logger` and use it

### Fix and enhancements

* Keep `git` / `subprocess` log records separated
* Prevent a strange issue when reloading logging module

## v14.8.1 (2024-04-02)

Diff: https://github.com/davidfischer-ch/pytoolbox/compare/14.8.0...14.8.1

### Migrations

* Replace your calls to `argparse.set_columns` by `console.set_columns`
* Replace your calls to `argparse.HelpArgumentParser` by `argparse.ArgumentParser`
* Replace your calls to `filesystem.recursive_copy` by `filesystem.copy_recursive`
* Replace your calls to `subprocess.git_clone_or_pull` by `git.clone_or_pull`
* Replace your calls to `subprocess.ssh` by `ssh.ssh`

### Features

* Prevent `pytoolbox` logged events being output to `sys.stderr` by registering a `NullHandler`
* Add class `argparse.ChainAction` (argument parsing action)
* Add function `argparse.separator` (argument parsing type)
* Add function `arpgarse.env_default` (utility function)
* Add convenient constants `DIRECTORY_ARGS`, `FILE_ARG`, `REMAINDER_ARG` and `MULTI_ARG()` (`arpgarse` module)
* Add class `argparse.ArgumentParser` (renamed from `argparse.HelpArgumentParser`)
* Add class `argparse.ActionArgumentParser`
* Add TypeAlias `Color`
* Expose `arpgarse.{ArgumentTypeError,Namespace}` to be convenient (`import argparse` not required)
* Decorator `decorators.deprecated` now accept a `guideline` argument (default to `''`)
* Expose `logging.{CRITICAL, ..., NOTSET}`, `logging.{Logger, LogRecord}` to be convenient (`import logging` not required)
* Add TypedDict `subprocess.CallResult` and use it to type hint functions response (added `exception` key)
* Function `subprocess.cmd`: Now logging to `pytoolbox.subprocess.cmd.<binary>` unless log is defined
* Function `subprocess.cmd`: Log can be a function, a `Logger` or a `str`. `None` will be mapped to default behavior

### Fix and enhancements

* Favor `type(obj)` over `obj.__class__`
* Class `exceptions.MessageMixin`: Now show missing attributes (attributes can be properties too)
* Class `exceptions.CalledProcessError`: Add property `cmd_short` and prevent exposing sensitive data in `__str__` or `__repr__`
* Fix calls to `yaml.dump` (as its now `ruamel.yaml`)
* Various improvements such as type hints, documentation, tests

## v14.8.0 (2024-03-25)

Diff: https://github.com/davidfischer-ch/pytoolbox/compare/14.7.0...14.8.0

### Minor compatibility breaks

* Replace `subprocess.CalledProcessError` by `exceptions.CalledProcessError`
* Rename function `subprocess.git_clone_or_pull` to `ssh.clone_or_pull` (keep a deprecated alias)
* Rename function `subprocess.ssh` to `ssh.ssh` (keep a deprecated alias)
* Rename TypeAlias `subprocess.LoggerType` to `logging.LoggerType`

### Migrations

* Replace your usage of `subprocess.CalledProcessError` by `exceptions.CalledProcessError`
* Replace your calls to `subprocess.git_clone_or_pull` by `ssh.clone_or_pull`
* Replace your calls to `subprocess.ssh` by `ssh.ssh`

### Features

* Add module `git`
* Add module `ssh`
* Add class `exceptions.CalledProcessError`
* Add class `exceptions.DuplicateGitTagError`
* Add class `exceptions.GitReferenceError`
* Add class `exceptions.RegexMatchGroupNotFoundError`
* Add class `exceptions.SSHAgentConnectionError`
* Add class `exceptions.SSHAgentLoadingKeyError`
* Add class `exceptions.SSHAgentParsingError`
* Add function `logging.get_logger`
* Add Protocol `logging.BasicLggerFunc`
* Add class `logging.BasicFuncLogger`
* Add function `regex.group_replace`
* Add TypeAlias `serialization.YamlDataTypes`
* Add function `serialization.get_yaml`
* Add function `serialization.to_yaml`
* Add decorator `unittest.skip_if_missing`

### Fix and enhancements

* Module `subprocess`: Now log defaulting to module's log
* Implement `__repr__` for exception classes
* Replace `pyyaml` by `ruamel.yaml`
* Cover `regex.Match` with tests
* Test code with `ruff`

## v14.7.0 (2024-03-22)

Diff: https://github.com/davidfischer-ch/pytoolbox/compare/14.6.0...14.7.0

### Minor compatibility breaks

* Drop Python 3.9 & 3.10 compatibility
* Favor `pathlib.Path` over `str`:
  * Returning `pathlib.Path` when its a path ...
  * Not accepting
* Force named arguments when it makes sense (`mypy` should help you with this)
* Drop `is_path` argument, instead check if its an instance of `pathlib.Path`:
  * Function `filesystem.from_template`
  * Function `filesystem.get_bytes`
* Rename argument `format` to `fmt` to fix a linter issue:
  * Function `datetime.datetime_now`
  * Function `datetime.datetime_to_str`
  * Function `datetime.str_to_datetime`
* Method `module.All.diff`: Drop argument `to_type`
* Function `network.http.download_ext_multi`: Argument `resources` must now be an iterable of `Resource`
* Functions `validation.valid_*`: Do not accept `None` anymore
* Rename function `filesystem.recursive_copy` to `filesystem.copy_recursive` (keep a deprecated alias)

### Deprecations

* Replace your calls to `filesystem.copy_recursive` by `filesystem.recursive_copy`

### Features

* Type hint a massive portion of code (and import annotations from __future__)!
* Ensure Python 3.11 & 3.12 compatibility
* Add optional MongoDB feature (`mongodb` extra)
* Add class `argparse.Namespace`
* Add context manager `filesystem.chdir`
* Add Protocol `filesystem.CopyProgressCallback`
* Add Protocol `filesystem.TemplateHookFunc`
* Add dataclass `network.http.Resource`
* Add Protocol `network.http.SingleProgressCallback`
* Add Protocol `network.http.MultiProgressCallback`
* Add TypeAlias `subprocess.CallArgType`
* Add TypeAlias `subprocess.CallArgsType`
* Add TypeAlias `subprocess.LoggerType`
* Add TypeAlias `types.GenericType`

### Fix and enhancements

* Add explicit named arguments `recursive`, `top_down`, `on_error`, `follow_symlinks`:
  * Function `filesystem.chown`
  * Function `filesystem.find_recursive`
* Add explicit named arguments related to `requests.get`:
  * Function `network.http.download_ext`
  * Function `network.http.iter_download_core`
  * Function `network.http.iter_download_to_file`
* Module `multimedia.ffmpeg`: Enhance it and make it compatible with ffmpeg 6.1 (See commit d026afdbbe86becbccb3c75d2a1830052834cd0a)
* Function `filesystem.copy_recursive`: Cover it with tests (See commit f4d5bd11992525d9fe08c56c668c254e7093f30d)
* Class `network.smpte2022.base`: Make it Python 3.9+ compatible (by Július Milan <julius.milan.22@gmail.com>)
* Class `types.StrongTypedMixin`: Make it compatible with future style annotations
* Module `multimedia.ffmpeg.miscellaneous`: Consolidate code (move common attributes to the parent class)
* Class `multimedia.ffmpeg.miscellaneous.Media`: Refactor it ()
* Refresh `__all__` and don't use magic when not necessary
* Switch from Travis CI to GitHub Actions
* Rework imports (drop multiple-imports *style*)
* Fix various linter issues
* Update `AUTHORS.md`

## v14.6.0 (2023-08-15)

Diff: https://github.com/davidfischer-ch/pytoolbox/compare/14.5.1...14.6.0

### Minor comptability breaks

* Functions `humanize.natural*`: Rename `format` arguments to `fmt`

### Features

* Module `humanize`: Add functions `parse_*`

### Fix and enhancements

* Ensure Python 3.11 compatibility
* Explain how to bother with GExiv2
* Add more type hints (especially `humanize` and `multimedia.exif`)
* Add `PyGObject` to requirements for `imaging` feature

## v14.5.1 (2023-06-08)

Diff: https://github.com/davidfischer-ch/pytoolbox/compare/14.5.0...14.5.1

### Fix and enhancements

* Make code compatible with legacy versions of `packaging`

## v14.5.0 (2023-06-07)

Diff: https://github.com/davidfischer-ch/pytoolbox/compare/14.4.0...14.5.0

### Minor compatibility breaks

* Bye bye Django 3 and less

### Features

* Make code compatible with Django 4+

### Fix and enhancements

* Usage of `super()` magic
* Upgrade testing stack especially pylint with its dozen tests
* Apply recommendations from linters (or silent it...)
* Convert Changelog and Authors in Markdown

## v14.4.0 (2022-12-09)

Diff: https://github.com/davidfischer-ch/pytoolbox/compare/14.3.0...14.4.0

### Minor compatibility breaks

* Replace `comparison.parse_version` by `comparison.try_parse_version` with a fallback behavior

### Features

* Add function `humanize.naturalweight`
* Add function `console.toggle_colors`
* Module `comparison`: Add `unified_diff`, `compare_versions` and `satisfy_version_constraints`

## Fix and enhancements

* Compatibility with latest Django releases
* Compatibility with latest `packaging` module (`LegacyVersion` was dropped)

## v14.3.0 (2022-09-09)

Diff: https://github.com/davidfischer-ch/pytoolbox/compare/14.2.0...14.3.0

### Minor compatibility breaks

* Drop Python 3.7 & 3.8 compatibility
* Drop `logging` extra (`termcolor` is now installed by default)

### Features

* Add [types.merge_annotations` class decorator
* Module `comparison`: Add `unified_diff`, `compare_versions` and `satisfy_version_constraints`

## v14.2.0 (2022-06-10)

Diff: https://github.com/davidfischer-ch/pytoolbox/compare/14.1.0...14.2.0

### Minor compatibility breaks

* Drop Python 3.6 compatibility
* Function `filesystem.from_template`: Make Jinja2 template strict with undefined values
* Module `argparse`: Return `pathlib.Path` instead of `str` (See commit 6acf8d13e2739a6e564b325bc035e33676c9ff07)

### Features

* Add some type hints (more to come)

## Fix and enhancements

* Convert some FIXMEs to TODOs
* Ensure Python 3.10 compatibility
* Fix many linter issues

## v14.1.0

Diff: https://github.com/davidfischer-ch/pytoolbox/compare/14.0.2...14.1.0

### Minor compatibility breaks

* Module `dango.models.fields`: Apply `NullifyMixin` to `StripCharField` and `StripTextField`

### Features

* Module `django.models.fields`: Add `NullifyMixin`, `CharField` and `TextField`

## Fix and enhancements

* Module `django.signals`: Fix `strip_strings_and_validate_model` not importable from `django.signals`
* Module `django.models.fields`: Fix `StripMixin` not fair play with inheritance

## v14.0.2

Diff: https://github.com/davidfischer-ch/pytoolbox/compare/14.0.1...14.0.2

## Fix and enhancements

* Fix Django deprecation warning (`ugettext_lazy` -> `gettext_lazy`)

## v14.0.1

Diff: https://github.com/davidfischer-ch/pytoolbox/compare/14.0.0...14.0.1

## Fix and enhancements

* Function `filesystem.from_template`: Add directories optional argument
* Fix Keras imports (because they changed)
* Fix newer pylint errors

## v14.0.0

Diff: https://github.com/davidfischer-ch/pytoolbox/compare/13.5.0...14.0.0

## Major compatibility breaks

* Drop Python 2.7 - 3.5 compatibility
* Drop module `encoding`
* Drop module `mongo`
* Drop function `network.http.get_request_data`
* Drop function `unittest.{mock_cmd,runtests}` (and dependency to nose)
* Remove unused arguments on some functions

### Minor compatibility breaks

* Function `multimedia.exif.brand.Brand.clean`: Raise `exceptions.InvalidBrandError`

### Features

* Rewrite code in Python 3 thanks to 2to3 and a lot of edits
* Rewrite tests in Python 3 and with pytest in replacement to unittest (and nose)
* Seamlessly download tests assets (small.mp4, ffmpeg, ffprobe) from S3
* Test on recent Python releases from 3.6 to 3.8 (3.9 will come next)
* Temporarily removed PyPy 3.6 from test matrix due to `tensorflow` (work in progress)

## Fix and enhancements

* setup.py an extra `all` one can install with pip install `.[all]`
* Separate requirements in three major groups: features, test and docs
* Make some functions compatible with `pathlib.Path` (work in progress)
* Check code quality with pylint and flake8 (they are top notch)
* Remove doctests boilerplate code and make them more robust
* Fix deprecation issues by reimplementing some functions
* Fix code smells and silent irrelevant warnings
* Update Travis CI configuration: Define distribution, update script, ...
* Generate documentation with `python setup.py docs`

## v13.5.0

### Minor compatibility breaks

* Class `multimedia.exif.miscellaneous.VideoStream`: Rename rotate to rotation

## Fix and enhancements

* Module `multimedia.exif`: Add Tamron brand

## v13.4.0

### Minor compatibility breaks

* Drop Python 2.6 + Python 3.2 support (remove from Travis CI build)
* Module `multimedia.ffmpeg`: Allow to pass input options (encoding)

## Fix and enhancements

* Module `multimedia.ffmpeg`: Refresh metadata classes
* Class `multimedia.exif.Metadata`: Allow to define path to save EXIF metadata

## v13.3.5

## Fix and enhancements

* Module `django`: Django 2.0 compatibility
* Module `filesystem`: Windows compatbility
* Class `django.models.fields.URLField`: Set max_length to 8000 by default
* Class `django.models.fields.\*`: Use `OptionsMixin` on all fields
* Add `requests` to requirements

## v13.3.0

## Fix and enhancements

* Function `filesystem.file_mime`: Convert to unicode only if required.

### Features

* Add module `pandas`

## v13.2.0

## Fix and enhancements

* Module `multimedia.exif`: Add Huawei.

### Features

* Add function `console.shell`

## v13.1.3

## Fix and enhancements

* Module `mutlimedia.exif`: Make classes swappable + importable from exif module.
* Module `smpte2022`: Fixed wraparound sequence number calculations for RTP and FEC.

Thanks to \@TobbeEdgeware!

## v13.1.1

### Minor compatibility breaks

* Function `serialization.object_to_dict`: Rely almost only on schema to produce output structure (hint: use list in schema)

## Fix and enhancements

* Function `collections.swap_dict_of_values`: Implement simple key-value swap.

## v13.0.4

## Fix and enhancements

* Function `aws.s3.remove_objects`: Add callback argument to make it more flexible.
* Function `multimedia.image.remove_transparency`: Enhance code (remove `force_rgb arg` from 13.0.2).
* Function `serialization.object_to_dict`: Add `iterable_callback` to customize container type of iterables.

## v13.0.0

## Compatibility breaks

* Remove fake bson's `ObjectId` (`private` module) when library not available.
* Function `filesystem.find_recursive` is now matching patterns against the whole path.
* Function `aws.s3.list_objects`: Handle multiple patterns like `filesystem.find_recursive`.
* Function `aws.s3.remove_objects`: Handle multiple patterns like `filesystem.find_recursive`.

### Features

* Add function `filesystem.to_user_id`
* Add function `filesystem.to_group_id`
* Add function `regex.from_path_patterns`

## Fix and enhancements

* Replace relative imports of `len(.) > 1` by absolute imports

## v12.2.3

### Features

* Add module `aws.s3`

## v12.1.2

## Compatibility breaks

* Remove `object_to_dict` and `object_to_dictV2`
* Rename `object_to_dictV3` to `object_to_dict`

## Fix and enhancements

* Move AI data to S3 (own account).
* Function `serialization.object_to_dict`: Also authorize to tweak obj (not only schema).
* Function `serialization.object_to_dict`: Also add depth information.
* Function `serialization.to_file`: Fix `to_file` not using `makedirs` properly

## v11.10.0

## Fix and enhancements

* Fix PEP-8 issue
* Class `django.models.fields.base.MoneyField`: Make decimal_places tweakable

### Features

* Add class `django.models.fields.mixins.LowercaseMixin`
* Add function `serialization.object_to_dictV3`

## v11.9.1

## Fix and enhancements

* Set line size to 100 chars and cleanup code
* Fix Travis build (remove `django` modules when testing)
* Always install pillow when installing with -e imaging
* Update README to reflect newer options
* Class `multimedia.exif.brand.Brand`: Add more brands
* Class `multimedia.exif.image.Orientation`: Use standard Enum, or object if not available

### Features

* Add module `ai`

## v11.8.6

### Fixes and enhancements

* Add `functions multimedia.image.PIL.{apply,get}_orientation`
* Add constant `ORIENTATION_TO_ROTATION` to `multimedia.exif.image.Image`
* Make function `multimedia.image.PIL.apply_orientation` more generic
* Make function `multimedia.image.PIL.apply_orientation` defaulting to nothing if orientation is crazy
* Make function `multimedia.image.PIL.get_orientation` more robust
* Class `exceptions.MessageMixin`: Fix pickle recursion error

### Features

* Add module `multimedia.image.PIL`
* Add function `types.merge_base_attribute`

## v11.7.6

### Minor compatibility breaks

* Remove jinja2 from packages installed by default

### Fixes and enhancements

* Support more Python versions (3.5, 3.6)
* Function `filesystem.makedirs`: Add parent argument
* Module `logging`: Update logging color scheme + make it overridable
* Module django.templatetags:
  * Implement `TEMPLATE_STRING_IF_INVALID` for Django \>= 1.8
  * Implement `include_is_allowed` for Django \>= 1.10
* `Class multimedia.exif.Metadata`: Can also read EXIF metadata from buffer
* Function `argparse.password`: Add it

## v11.7.1

### Minor compatibility breaks

* Remove unnecessary dependencies + put some as extra

### Fixes and enhancements

* Module `filesystem`: Add `walk_kwargs` to some functions
* Function `logging.setup_logging`: make possible to setup an instance of logger

## v11.6.4

### Fixes and enhancements

* Module `argparse`: Set columns to a value or auto-detected
* Module `exif`: Fix orientation is not value from Orientation
* Module `smpte2022`: Various fixes by @AbdulTheProgrammer
* Enhance function `logging.setup_logging`:
  * Add optional colorized mode
  * Always setup log level and return logger
* Enhance module `multimedia.exif`:
  * Add optional orientation override
  * Add rotation property based on orientation
  * Add rewrite method to fix issues with exif tags
  * Allow to specify gexiv2 version
* Use iteritems because its still a Python 2 (and 3) library

## v11.6.0

### Fixes and enhancements

* Add method `get_frames_md5_checksum` to `FFmpeg` class
* Update exif brands

### Features

* Support Python 3.6
* Add function `itertools.chunk`

## v11.5.4

### Fixes and enhancements

* Fix syntax error in `multimedia.exif.lens` at line 22
* Prevent `AppRegistryNotReady` when importing `django.models.utils`
* Add `{pre,post}_func` arguments to `filesystem.from_template`
* Function `filesystem.from_template`: Make destination optional + allow to set template to content

### Features

* Add function `crypto.get_password_generator`

## v11.5.0

### Fixes and enhancements

* Improve code quality
* Remove `try_` prefix from `filesystem` functions (retro compat: `try_` functions still defined)

## v11.4.3

### Features

* Add constant `encoding.integer_types`
* Add function `subprocess.su`
* Add function `types.get_arguments_names`

### Fixes and enhancements

* Add bare argument to `subprocess.git_clone_or_pull`

## v11.4.0

### Features

* Add module `linux`
* Add module `setuptools`

## v11.2.0

### Features

* Add classes `types.Echo{Object,Dict}`
* Add classes `argparse.Help{ArgumentParser,Formatter}`

### Fixes and enhancements

* Add docstrings and fix doctests
* Fix `django.forms.utils.get_instance`
* Update `FromPrivateKeyMixin` to fix call to fail with recent DRF

## v11.1.0

### Minor compatibility breaks

* Update `git_clone_or_pull` to full clone by default

### Features

* Add module `network.url`
* Add mixin `django.forms.mixins.CreatedByMixin`
* Add mixin `django.forms.mixins.StaffOnlyFieldsMixin`

### Fixes and enhancements

* Add/fix docstrings and unit-tests
* Use `xrange` and `iter{items,keys,values}` under Python 2
* Replace `nose.tools` by `pytoolbox.unittest.asserts`
* Make `RequestMixin` more transparent
* `network.http.download_ext`: Pass `kwargs` to `iter_download_to_file`
* `django.views.mixins.AddRequestToFormKwargsMixin`: Check form "handles" request as `kwarg` based on its class

## v11.0.0

## Compatibility breaks

* Remove ming module to cleanup build
* Remove `django.models.mixins.PublishedMixin` (not generic enough neither powerful enough)

### Minor compatibility breaks

* Prefer path over filename (arguments convention)
* Replace `MapUniqueTogetherMixin` + `MapUniqueTogetherIntegrityErrorToValidationErrorMixin` by `BetterUniquenessErrorsMixin`.
* Move `CancellableDeleteView` to `django.views.base`

### Features

* Generate documentation and publish on readthedocs.org
* Add mixin `django.models.mixins.BetterUniquenessErrorsMixin`

### Fixes and enhancements

* Add/fix docstrings
* Update modules headers
* Make `django.views.mixins.ValidationErrorsMixin` more "generic"
* Too many to be listed here, https://github.com/davidfischer-ch/pytoolbox/compare/10.4.0...11.0.0

## v10.4.0

### Features

* Add module `django.models.metaclass`
* Add module `django.views.utils`
* Add module `enum`
* Add modules in `multimedia.exif`:
  * `brand`
  * `camera`
  * `equipement`
  * `image`
  * `lens`
  * `photo`
  * `tag`
* Add module `rest_framework.metadata.mixins`
* Add mixin `django.models.mixins.PublicMetaMixin`
* Add decorator `decorators.cached_property`
* Add decorator `decorators.hybridmethod`
* Add functions in `django.models.utils`:
  * `get_related_manager`
  * `get_related_model`
  * `try_get_field`
* Add function `types.get_properties`

### Fixes and enhancements

* Handle 24h+ hour format in `datetime.str_to_datetime`
* Module `django.forms.utils` imports from `django.forms.utils` module
* Fix `ReloadMixin` popping update_fields!
* Refactor class `multimedia.exif.metadata.Metadata` (use newest classes)
* Split module `multimedia.ffmpeg`
* Fix `ffmpeg`'s' `mock` class

## v10.3.0

## Compatibility breaks

* Remove module `rest_framework.v2`
* Refactor (optimize) `unittest.FilterByTagsMixin`

### Minor compatibility breaks

* Rename module `exception` to `exceptions`
* Rename module `rest_framework.v3` to `rest_framework`
* Rename some attributes of `multimedia.ffmpeg` classes

### Features

* Add many modules:
  * `atlassian`
  * `itertools`
  * `module` (yes!)
  * `selenium`
  * `signals`
  * `states`
  * `string`
  * `voluptuous`
* Add class `argparse.Range`
* Add function `argparse.multiple`
* Add function `collections.{merge_dicts, swap_dict_of_values}`
* Add decorator `decorators.run_once`
* Add modules and mixins in `django\*` module
* Add value `encoding.binary_type`
* Add function `humanize.naturalfrequency`
* Add function `types.isiterable`
* Add classes `types.{DummyObject,MissingType}`
* Add object `types.Missing instance of MissingType`
* Add mixins `unittest.{InMixin,InspectMixin}`
* Add class `unittest.Asserts`
* Add object `unittest.asserts`

### Fixes and enhancements

* Countless fixes and enhancements
* Follow `os.path` import best practices
* Make `multimedia.ffmpeg` private functions public

## v10.2.0

## Compatibility breaks

* Add `EncodeStatistics` and refactor `FFmpeg.encode()`

### Minor compatibility breaks

* Merge `django.template` tags & filters into 1 file
* Split `FFmpeg` class to `FFmpeg` + `FFprobe` classes

### Features

* Add module `django.exceptions`
* Add `static_abspath` Django template tag
* Add class `django.forms.mixins.EnctypeMixin`
* Add class `django.models.mixins.AlwaysUpdateFieldsMixin`
* Add class `django.models.mixins.AutoForceInsertMixin`
* Add class `django.models.mixins.AutoUpdateFieldsMixin`
* Add class `django.models.mixins.MapUniqueTogetherIntegrityErrorToValidationErrorMixin`
* Add class `django.models.mixins.RelatedModelMixin`
* Add class `django.models.mixins.UpdatePreconditionsMixin`
* Add class `django.storage.ExpressTemporaryFileMixin`
* Add class `django.test.mixins.FormWizardMixin`
* Add class `django.views.mixins.InitialMixin`
* Add class `logging.ColorizeFilter`
* Add function `collections.flatten_dict`
* Add function `datetime.multiply_time`

### Fixes and enhancements

* Avoid hardcoding `\n`
* Module `console`: Write to given stream
* Module `datetime`: Make API more consistent
* Module `multimedia.ffmpeg`:
  * Split `FFmpeg` class in `FFmpeg` and `FFprobe`
  * Add `EncodeState` & `EncodeStatistics` classes
  * Do some analysis before launching `ffmpeg` subprocess
  * Fix progress if sub-clipping
  * Improve handling of `media` argument
  * Miscellaneous improvements
* Module `subprocess`: Import Popen from psutil if available
* Refactor function `django.signals.create_site`

## v10.0.0

## Compatibility breaks

* Method `multimedia.ffmpeg.FFmpeg.encode` always yields at start

### Features

* Add some mixins in `rest_framework.v*.views.mixins`

### Fixes and enhancements

* Add class `multimedia.ffmpeg.EncodingState`

## v9.7.2

### Minor compatibility breaks

* Function `filesystem.get_bytes` returns a generator
* Rename all functions with `_to_` instead of `2` (e.g. `str2time` -> `str_to_time`)
* Rename some methods of the class `ffmpeg.FFmpeg`
* Change signature of `console` module's functions

### Features

* Add module `comparison`
* Add module `regex`
* Add module `types`
* Add class `filesystem.TempStorage`
* Add function `exception.get_exception_with_traceback`
* Add function `humanize.natural_int_key`
* Add function `console.progress_bar`

### Fixes and enhancements

* Add `streams` methods to `ffmpeg.FFmpeg`
* Improve `ffmpeg` module (add `Media` class for inputs/outputs)
* Improve `network.http.download_ext` (Can download in chunks + progress callback)
* Improve `filesystem.get_bytes` + `crypto.*` to read a file in chunks (if `chunk_size` is set)

## v9.4.2

### Features

* Add module `humanize`
* Add module `django.models.query.mixins`
* Add module `django.test.runner.mixins`

### Fixes and enhancements

* Add `__all__` to make the API explicit
* Add method `get_media_framerate` to `FFmpeg` class
* Add module `private` (with `_parse_kwargs_string`)
* `network` module: Cleaner usage of `string.format()`
* Refactor module `humanize` + add `naturalfilesize`
* Improve `humanize` functions to handle `[0-1]` range + big numbers

## v9.3.0-beta

## Compatibility breaks

* Refactor `multimedia` modules
* Rename module `django.templatetags.pytoolbox_tags` to `_filters`

### Minor compatibility breaks

* Rename `django.forms` -> `django.forms.mixins`
* Rename `django.views` -> `django.views.mixins`

### Features

* Add module `django.templatetags.pytoolbox_tags`
* Add module `multimedia.exif`
* Add some `django mixins`

### Fixes and enhancements

* Fix unicode handling
* Function `datetime.total_seconds` now accept instance of `timedelta`
* Function `filesystem.from_template` can now use jinja2 to generate the content
* `timedelta` & `to_filesize` Django template filters now handle empty string input
* Add argument `create_out_directory` to method `multimedia.ffmpeg.FFmpeg.encode`
* Fix `multimedia.ffmpeg.FFmpeg.encode`: Create output directory before the subprocess
* Improve `multimedia.ffmpeg.FFmpeg.encode`: Handle process missing + simplify mocking

## v8.6.1-beta

### Fixes and enhancements

* Add function `multimedia.ffmpeg.get_subprocess`

## v8.6.0-beta

### Minor compatibility breaks

* Rename module `django.models` -> `django.models.mixins`

### Features

* Add module `django.models.fields`
* Add class `validation.CleanAttributesMixin`
* Add class `validation.StrongTypedMixin`
* Add class `django.forms.RequestMixin`
* Add class `django.views.AddRequestToFormKwargsMixin`
* Add class `django.views.LoggedCookieMixin`
* Add class `unittest.AwareTearDownMixin`
* Add function `subprocess.git_add_submodule`
* Add function `network.http.download_ext`
* Add function `datetime.parts_to_time`

### Fixes and enhancements

* Add some classes in module `exception`
* Add module `django.urls` with utility regular expressions
* Improve `crypto.githash` to handle reading data from a file
* Fix `SaveInstanceFilesMixin` (use .pk instead of .id)
* Improve `datetime.str2time` to handle microseconds
* Improve `filesystem.try_remove` to handle directories (when `recursive=True`)
* Improve `multimedia.ffprobe.get_media_duration` (return None in case of error)
* `StrongTypedMixin`: Allow setting arg to the default value (if set)
* Split `HelpTextToPlaceholderMixin` logic to allow modify behavior by inheritance
* Fix `multimedia.ffmpeg.encode` (convert default_in_duration to time)
* Fix `multimedia.ffmpeg.encode` (may return None - out_duration)
* Fix `multimedia.ffmpeg.encode` (skip broken out duration)
* Improve `multimedia.ffprobe.get_media_duration` to handle media info dict

## v8.0.0-beta

## Compatibility breaks

* Move `ffmpeg` and `x264` modules into `multimedia`
* Replace unreliable `ffmpeg.get_media_*` functions by `multimedia.ffprobe.get_media_*`

### Features

* Add module `multimedia.ffprobe`
* Add function `datetime.str2time`

## v7.1.17-beta

## Compatibility breaks

* Store command line arguments in `args` attribute, do not update `__dict__` of the instance.

### Features

* Add module `argparse`

### Fixes and enhancements

* Add function `argparse.is_file`
* Add `cleanup` argument to `juju.boostrap`
* Add docstring to function `juju.ensure_num_units`
* Add `get_unit_public_address` + `properties` methods to class `juju.Environment` (thanks @smarter)
* Add args and namespace kwargs to `juju.DeploymentScenario.__init__` to allow bypassing `sys.arv`
* Fix various bugs of `juju` module + various updates according to juju 1.18
* Fix `subprocess.rsync`
* Fix `crypto.githash`
* Fix handling of juju bootstrap error message in Python 3
* Default to something if key is missing in stats (x264.encode)
* Use sudo with juju status (to work around https://bugs.launchpad.net/juju-core/+bug/1237259)
* Add timeout to valid_uri

## v6.6.0-beta

## Compatibility breaks

* Improve errors and time-outs handling in `juju` module (for the best)
* Move socket & twisted fec generators to `pytoolbox_bin`

### Minor compatibility breaks

* Remove deprecated `flask.get_request_data` (replaced by `network.http.get_requests_data`)
* `SmartJSONEncoderV2` now filter the class attributes
* Fix `SmartJSONEncoderV2`!

### Features

* Add module `decorators`
* Add module `django.utils`
* Add module `x264`
* Add function `datetime.secs_to_time`
* Add function `datetime.time_ratio`
* Add function `ffmpeg.get_media_resolution`
* Add function `mongo.mongo_do`
* Add function `network.http.download`
* Add function `subprocess.git_clone_or_pull`

### Fixes and enhancements

* Fix `test_ensure_num_units`, `str2datetime`
* Fix computation of `FecReceiver.lostogram`
* Fix usage of `time_ratio` by `ffmpeg` and `x264` modules
* Use renamed IP class (previously `IPAddress`) fallback import to `IPAddress`
* Accept None to leave owner or group unchanged (`filesystem.chown`)
* Set default time-outs to None and update juju module (fixes)
* Add some arguments to `recursive_copy` and `rsync`
* Append sudo to juju bootstrap
* Add `juju.Environment.wait_unit`
* Improve `ffmpeg` module

## v5.6.3-beta

### Fixes and enhancements

* Add timeout argument to `cmd()`
* Remove symlink first, to avoid boring exceptions
* Add timeout to juju status !

## v5.6.0-beta

### Features

* Add function `validation.valid_int()`

### Fixes and enhancements

* Add constants to `juju` module
* Juju bootstrap will print time as int
* Add `makedirs` argument to some methods of the objects of `serialization`
* Add user argument to function `subprocess.cmd`
* Add path argument to `subprocess.make`
* Add extra_args (list) to function `subprocess.rsync`
* Fix `juju`, `serialization`, `subprocess` modules, update tests
* Function subprocess.cmd : Handle `logging.Logger` as log, improve docstring, add retry loop
* Upgrade `relation_` methods

## v5.5.0-beta

### Minor compatibility breaks

* Move all django template tags into module `pytooblox_tags`
* Move `juju` functions to the `Environment` class

### Features

* Add `console.choice()` (by kyouko-taiga)
* Add function `serialization.to_file` and use it to improve `PickeableObject` and `JsoneableObject` write methods.

### Fixes and enhancements

* Add missing MANIFEST.in
* Add new django-related modules
* Add some django mixins + template tags
* Make class `django.models.GoogleMapsMixin` more generic
* Add cli_output argument to `subprocess.cmd`
* Add size_only argument to `subprocess.rsync`
* Do not add hashlib to requirements if already part of the stdlib
* Fix headers + rest markup + update title
* Enhance function `ffmpeg.encode`
* Call log more often

## v5.4.19-beta

### Deprecated

* `flask.get_request_data` replaced by `network.http.get_request_data`

### Minor compatibility breaks

* Split `django` module into submodules
* Rename `SmartModel` to `AbsoluteUrlMixin`

### Features

* Embed `smpte2022lib`
* Add entry points (`socket-fec-generator` + ` twisted-fec-generator`)
* Add commit and release scripts to make it more securely (run tests before, check sphinx ...)
* Add module `network.http` and classes `juju.SimulatedUnit(s)`
* Add module `django.templatetags` with getattribute function
* Add class `django.models.SaveInstanceFilesMixin`
* Add function `django.forms.update_widget_attributes`

### Fixes and enhancements

* Lighter list of dependencies
* Add `--extra-...` flags to install dependencies for the extra features/modules.
* Filter packages to avoid installing tests module !
* Fix `setup.py` to avoid removing tests from packages list if it did not exist.
* Add kwargs to `serialization.object2json` -> `json.dumps`
* `map_marker` : Convert to unicode sooner (to handle special field class)
* `django.forms.SmartModelForm` : Attributes & replacement class applied depending of the form field's class
* Add fill option to `collections.pygal_deque.list()`
* Replace range by xrange, values by itervalues, ...
* Handle `datetime.date` class (function `datetime.dateime2epoch`)
* Add suffix parameter to `AbsoluteUrlMixin.get_absolute_url`
* Ensure import from future of great things
* Fix docstrings

Example usage:

```
sudo python setup.py install --help
sudo python setup.py install --extra-flask
```

## v5.0.0-beta

## Compatibility breaks

* Remove `py_` prefix of all modules & paths
* Change license (GNU GPLv3 -> EUPL 1.1)

### Features

* Add module `mongo`

### Fixes and enhancements

* Use absolute imports
* Update classifiers
* Update README.rst

## v4.8.7-beta

### Minor compatibility breaks

* Rename `duration2secs` -> `total_seconds`
* Rename `get_request_json` -> `get_request_data`

### Features

* Python 3 support
* Add module `py_collections`
* Add module `py_django`
* Add function `json_response2dict`
* Add function `make`
* Add function `ssh`
* Greatly improve module `py_juju`
* Greatly improve module `py_serialization`

### Fixes and enhancements

* Update README.rst
* Update function `get_request_data`
* Update function `map_exceptions`
* Update function `runtests`
* Update `setup.py`

## v4.0.0-beta

## Compatibility breaks

* Greatly improve module `py_serialization`

### Features

* Greatly improve module `py_juju`
* Add class `TimeoutError`
* Add function `print_error`

### Fixes and enhancements

* Fix `setup.py`
* Update `cmd`
* Update `rsync`

## v3.10.7-beta

## Compatibility breaks

* Rename module `py_mock` -> `py_unittest`
* Remove function `unicode_csv_reader`

### Features

* Add module `py_console`
* Add module `py_unicode`
* Add module and function `runtests`
* Add class `JsoneableObject`
* Add function `assert_raises_item`
* Add function `valid_uri`
* Add function `validate_list`
* Greatly improve module `py_juju`
* Greatly improve setup and unit-testing

### Fixes and enhancements

* Fix shebangs
* Handle unicode
* Use new string formatting
* Update function map_exceptions
* Add kwargs to functions of module `py_subprocess`
