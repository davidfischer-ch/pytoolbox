"""Tests for the django.templatetags package."""

from __future__ import annotations

import subprocess
import sys
import textwrap


def test_string_if_invalid_is_the_django_templates_option() -> None:
    """string_if_invalid holds the option of the first engine of the DjangoTemplates type."""
    script = textwrap.dedent(
        """
        import django
        from django.conf import settings
        from django.template.backends.django import DjangoTemplates


        class ProjectTemplates(DjangoTemplates):
            pass


        settings.configure(
            TEMPLATES=[
                {'BACKEND': 'django.template.backends.jinja2.Jinja2', 'OPTIONS': {}},
                {
                    'BACKEND': '__main__.ProjectTemplates',
                    'OPTIONS': {'string_if_invalid': 'INVALID'},
                },
            ],
        )
        django.setup()

        from pytoolbox.django import templatetags

        print(templatetags.string_if_invalid)
        """
    )
    assert (
        subprocess.run(
            [sys.executable, '-c', script],
            capture_output=True,
            check=True,
            text=True,
        ).stdout.strip()
        == 'INVALID'
    )
