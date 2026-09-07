"""
Mix-ins for building your own views.
"""
# pylint: disable=protected-access,too-few-public-methods

from __future__ import annotations

import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from django.contrib import messages
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import models
from django.shortcuts import redirect
from django.views.generic import base as generic

from pytoolbox import module
from pytoolbox.compat import override
from pytoolbox.django.core import exceptions
from pytoolbox.django.forms import mixins as forms_mixins
from pytoolbox.django.models import utils

if TYPE_CHECKING:
    from django import forms
    from django.http import HttpRequest, HttpResponse, HttpResponseBase
    from django.views.generic.edit import ModelFormMixin, ProcessFormView

    class _ViewsMixin(ModelFormMixin, ProcessFormView):
        """
        The class-based view surface the mixins below complete.

        They read the view's request, its dispatch chain and its form handling, so this states
        that requirement for the checker; at runtime they stay plain mixins, to be placed to
        the left of the view class they complete.
        """

else:
    _ViewsMixin = object

_all = module.All(globals())


class AddRequestToFormKwargsMixin(_ViewsMixin):
    """Add the view request to the keywords arguments for instantiating the form."""

    @override
    def get_form_kwargs(self, *args: Any, **kwargs: Any) -> dict[str, object]:
        """Add the request to form kwargs if the form is a :class:`RequestMixin`."""
        kwargs = super().get_form_kwargs(*args, **kwargs)
        if self.should_add_request_to_form_kwargs():
            kwargs.update({'request': self.request})
        return kwargs

    def should_add_request_to_form_kwargs(self) -> bool:
        """
        Check whether the form class is a
        :class:`~pytoolbox.django.forms.mixins.RequestMixin`.
        """
        return issubclass(self.get_form_class(), forms_mixins.RequestMixin)


class BaseModelMultipleMixin(_ViewsMixin):
    """Derive context object name from the base model of the queryset."""

    @override
    def get_context_object_name(self, obj: Any) -> str:
        """Get the name of the item to be used in the context."""
        if self.context_object_name:
            return self.context_object_name
        if hasattr(obj, 'model'):
            return f'{utils.get_base_model(obj.model)._meta.model_name}_list'
        return ''


class BaseModelSingleMixin(_ViewsMixin):
    """Derive context object name from the base model of the instance."""

    @override
    def get_context_object_name(self, obj: Any) -> str:
        """Get the name to use for the instance."""
        if self.context_object_name:
            return self.context_object_name
        if isinstance(obj, models.Model):
            return utils.get_base_model(obj)._meta.model_name or ''
        return ''


class InitialMixin(_ViewsMixin):
    """Add helpers to safely use the URL query string to fill a form with initial values."""

    initials = {}

    @override
    def get_initial(self) -> dict[str, object]:
        """Populate initial form values from :attr:`initials` and query string."""
        initial = super().get_initial()
        for name, default in self.initials.items():
            self.set_inital(initial, name, default)
        return initial

    def set_inital(self, initial: dict[str, object], name: str, default: object) -> object:
        """Set an initial value from the query string or fall back to *default*."""
        initial[name] = value = self.request.GET.get(name, default)
        return value

    def set_initial_from_func(
        self,
        initial: dict[str, object],
        name: str,
        default: object,
        func: Callable[..., Any],
        msg_value: str,
        mgs_missing: str,
    ) -> object:
        """Set an initial value by applying *func* to the query string parameter."""
        value = self.request.GET.get(name, default)
        if value is not default:
            try:
                value = func(value)
            except ValueError:
                messages.error(self.request, f'{name} - {msg_value}.')
                return None
            except KeyError:
                messages.error(self.request, f'{name} - {mgs_missing}.')
                return None
        initial[name] = value
        return value

    def set_initial_from_model(
        self,
        initial: dict[str, object],
        name: str,
        default: object,
        model: type[models.Model],
        msg_value: str,
        mgs_missing: str,
    ) -> object:
        """Set an initial value by looking up a model instance by primary key."""
        value = self.request.GET.get(name, default)
        if value is not default:
            try:
                # The caller's model is expected to expose a per-user manager.
                manager = model.objects
                value = manager.for_user(self.request.user).get(pk=value)  # pyrefly: ignore
            except ValueError:
                messages.error(self.request, f'{name} - {msg_value}.')
                return None
            except model.DoesNotExist:
                messages.error(self.request, f'{name} - {mgs_missing}.')
                return None
        initial[name] = value
        return value


class LoggedCookieMixin(_ViewsMixin):
    """Add a "logged" cookie set to "True" if user is authenticated else to "False"."""

    @override
    def post(self, *args: Any, **kwargs: Any) -> HttpResponse:
        """Set a ``logged`` cookie reflecting the user's authentication state."""
        response = super().post(*args, **kwargs)
        logged = self.request.user.is_authenticated
        # Django types the value as a string but stringifies whatever it is given.
        value = logged if isinstance(logged, bool) else logged()
        response.set_cookie('logged', value)  # pyrefly: ignore[bad-argument-type]
        return response


class RedirectMixin(_ViewsMixin):
    """Redirect to a page."""

    redirect_view = None

    @override
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        """Redirect to :attr:`redirect_view` if set, otherwise dispatch normally."""
        if self.redirect_view:
            return redirect(self.redirect_view)
        return super().dispatch(request, *args, **kwargs)


class TemplateResponseMixin(generic.TemplateResponseMixin):
    """Resolve template names from a directory and action, with a default fallback."""

    default_template_directory = 'default'

    # Supplied by the view: where its templates live and which action is being rendered.
    template_directory: str
    action: str

    @override
    def get_template_names(self) -> list[str]:
        """Return template candidates based on :attr:`template_directory` and action."""
        return (
            [self.template_name]
            if self.template_name
            else [
                os.path.join(self.template_directory, self.action + '.html'),
                os.path.join(self.default_template_directory, self.action + '.html'),
            ]
        )


class ValidationErrorsMixin(_ViewsMixin):
    """
    Catch :class:`~django.core.exceptions.ValidationError` during save
    and re-display the form.
    """

    @override
    def form_valid(self, form: forms.Form) -> HttpResponse:
        """Catch :class:`~django.core.exceptions.ValidationError` and re-display the form."""
        try:
            return super().form_valid(form)
        except ValidationError as exc:
            for field, error in exceptions.iter_validation_errors(exc):
                if field:
                    form.add_error(field, error)
                else:
                    self._handle_unknown_error(form, error)
            return self.form_invalid(form)

    def _handle_unknown_error(self, form: forms.Form, error: ValidationError) -> None:
        form.add_error(NON_FIELD_ERRORS, error)


__all__ = _all.diff(globals())
