# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2015 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pytoolbox Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function, unicode_literals

import os

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import models
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic.edit import DeleteView

from ..models import utils
from ... import module

_all = module.All(globals())


class AddRequestToFormKwargsMixin(object):
    """Add the view request to the keywords arguments for instantiating the form."""

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(AddRequestToFormKwargsMixin, self).get_form_kwargs(*args, **kwargs)
        kwargs.update({'request': self.request})
        return kwargs


class BaseModelMultipleMixin(object):

    def get_context_object_name(self, instance_list):
        """Get the name of the item to be used in the context."""
        if self.context_object_name:
            return self.context_object_name
        elif hasattr(instance_list, 'model'):
            return '{0}_list'.format(utils.get_base_model(instance_list.model)._meta.model_name)


class BaseModelSingleMixin(object):

    def get_context_object_name(self, instance):
        """Get the name to use for the instance."""
        if self.context_object_name:
            return self.context_object_name
        elif isinstance(instance, models.Model):
            return utils.get_base_model(instance)._meta.model_name


class CancellableDeleteView(DeleteView):
    """Handle the cancel action (detect a cancel parameter in the POST request)."""

    def post(self, request, *args, **kwargs):
        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.success_url)
        return super(CancellableDeleteView, self).post(request, *args, **kwargs)


class InitialMixin(object):
    """Add helpers to safely use the URL query string to fill a form with initial values."""

    initials = {}

    def get_initial(self):
        initial = super(InitialMixin, self).get_initial()
        for name, default in self.initials.items():
            self.set_inital(initial, name, default)
        return initial

    def set_inital(self, initial, name, default):
        initial[name] = value = self.request.GET.get(name, default)
        return value

    def set_initial_from_func(self, initial, name, default, func, msg_value, mgs_missing):
        value = self.request.GET.get(name, default)
        if value is not default:
            try:
                value = func(value)
            except ValueError:
                messages.error(self.request, '{0} - {1}.'.format(name, msg_value))
                return None
            except KeyError:
                messages.error(self.request, '{0} - {1}.'.format(name, mgs_missing))
                return None
        initial[name] = value
        return value

    def set_initial_from_model(self, initial, name, default, model, msg_value, mgs_missing):
        value = self.request.GET.get(name, default)
        if value is not default:
            try:
                value = model.objects.for_user(self.request.user).get(pk=value)
            except ValueError:
                messages.error(self.request, '{0} - {1}.'.format(name, msg_value))
                return None
            except model.DoesNotExist:
                messages.error(self.request, '{0} - {1}.'.format(name, mgs_missing))
                return None
        initial[name] = value
        return value


class LoggedCookieMixin(object):
    """Add a "logged" cookie set to "True" if user is authenticated else to "False"."""

    def post(self, *args, **kwargs):
        response = super(LoggedCookieMixin, self).post(*args, **kwargs)
        response.set_cookie('logged', self.request.user.is_authenticated())
        return response


class RedirectMixin(object):
    """Redirect to a page."""

    redirect_view = None

    def dispatch(self, request, *args, **kwargs):
        if self.redirect_view:
            return redirect(self.redirect_view)
        return super(RedirectMixin, self).dispatch(request, *args, **kwargs)


class TemplateResponseMixin(object):

    default_template_directory = 'default'

    def get_template_names(self):
        return [self.template_name] if self.template_name else [
            os.path.join(self.template_directory, self.action + '.html'),
            os.path.join(self.default_template_directory, self.action + '.html')
        ]


class ValidationErrorsMixin(object):

    def form_valid(self, form):
        try:
            return super(ValidationErrorsMixin, self).form_valid(form)
        except ValidationError as e:
            for field, error in e.error_dict.items():
                form.add_error(field, error)
            return self.form_invalid(form)

__all__ = _all.diff(globals())
