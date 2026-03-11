"""
Mix-ins for building your own views.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING
import os

from django.contrib import messages
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import models
from django.shortcuts import redirect
from django.views.generic import base as generic

from pytoolbox import module
from pytoolbox.django.core import exceptions
from pytoolbox.django.forms import mixins as forms_mixins
from pytoolbox.django.models import utils

if TYPE_CHECKING:
    from django import forms
    from django.http import HttpRequest, HttpResponse

_all = module.All(globals())


class AddRequestToFormKwargsMixin:
    """Add the view request to the keywords arguments for instantiating the form."""

    def get_form_kwargs(self, *args: object, **kwargs: object) -> dict[str, object]:
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


class BaseModelMultipleMixin:
    """Derive context object name from the base model of the queryset."""

    def get_context_object_name(self, instance_list: object) -> str | None:
        """Get the name of the item to be used in the context."""
        if self.context_object_name:
            return self.context_object_name
        if hasattr(instance_list, 'model'):
            return f'{utils.get_base_model(instance_list.model)._meta.model_name}_list'
        return None


class BaseModelSingleMixin:
    """Derive context object name from the base model of the instance."""

    def get_context_object_name(self, instance: object) -> str | None:
        """Get the name to use for the instance."""
        if self.context_object_name:
            return self.context_object_name
        if isinstance(instance, models.Model):
            return utils.get_base_model(instance)._meta.model_name
        return None


class InitialMixin:
    """Add helpers to safely use the URL query string to fill a form with initial values."""

    initials = {}

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
            func: Callable,
            msg_value: str,
            mgs_missing: str
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
            mgs_missing: str
    ) -> object:
        """Set an initial value by looking up a model instance by primary key."""
        value = self.request.GET.get(name, default)
        if value is not default:
            try:
                value = model.objects.for_user(self.request.user).get(pk=value)
            except ValueError:
                messages.error(self.request, f'{name} - {msg_value}.')
                return None
            except model.DoesNotExist:
                messages.error(self.request, f'{name} - {mgs_missing}.')
                return None
        initial[name] = value
        return value


class LoggedCookieMixin:
    """Add a "logged" cookie set to "True" if user is authenticated else to "False"."""

    def post(self, *args: object, **kwargs: object) -> HttpResponse:
        """Set a ``logged`` cookie reflecting the user's authentication state."""
        response = super().post(*args, **kwargs)
        logged = self.request.user.is_authenticated
        response.set_cookie('logged', logged if isinstance(logged, bool) else logged())
        return response


class RedirectMixin:
    """Redirect to a page."""

    redirect_view = None

    def dispatch(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        """Redirect to :attr:`redirect_view` if set, otherwise dispatch normally."""
        if self.redirect_view:
            return redirect(self.redirect_view)
        return super().dispatch(request, *args, **kwargs)


class TemplateResponseMixin(generic.TemplateResponseMixin):
    """Resolve template names from a directory and action, with a default fallback."""

    default_template_directory = 'default'

    def get_template_names(self) -> list[str]:
        """Return template candidates based on :attr:`template_directory` and action."""
        return [self.template_name] if self.template_name else [
            os.path.join(self.template_directory, self.action + '.html'),
            os.path.join(self.default_template_directory, self.action + '.html')
        ]


class ValidationErrorsMixin:
    """
    Catch :class:`~django.core.exceptions.ValidationError` during save
    and re-display the form.
    """

    def form_valid(self, form: forms.Form) -> HttpResponse:
        """Catch :class:`~django.core.exceptions.ValidationError` and re-display the form."""
        try:
            return super().form_valid(form)
        except ValidationError as ex:
            for field, error in exceptions.iter_validation_errors(ex):
                if field:
                    form.add_error(field, error)
                else:
                    self._handle_unknown_error(form, error)
            return self.form_invalid(form)

    def _handle_unknown_error(self, form: forms.Form, error: ValidationError) -> None:
        form.add_error(NON_FIELD_ERRORS, error)


__all__ = _all.diff(globals())
