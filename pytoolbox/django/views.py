# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2014 David Fischer. All rights reserved.
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

from django.http import HttpResponseRedirect
from django.views.generic.edit import DeleteView


def only_published(queryset, request):
    """
    Filter the queryset to remove the unpublished entries if the user is not authenticated and the model does have a
    published field, defaults to the unfiltered queryset.
    """
    if not request.user.is_authenticated():
        try:
            return queryset.filter(published=True)
        except:
            # FIXME a better way to handle models w/o published attribute
            return queryset
    else:
        return queryset


class AddRequestToFormKwargsMixin(object):
    """Add the view request to the keywords arguments for instantiating the form."""

    def get_form_kwargs(self):
        kwargs = super(AddRequestToFormKwargsMixin, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs


class CancellableDeleteView(DeleteView):
    """Handle the cancel action (detect a cancel parameter in the POST request)."""

    def post(self, request, *args, **kwargs):
        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.success_url)
        return super(CancellableDeleteView, self).post(request, *args, **kwargs)


class LoggedCookieMixin(object):
    """Add a "logged" cookie set to "True" if user is authenticated else to "False"."""

    def post(self, *args, **kwargs):
        response = super(LoggedCookieMixin, self).post(*args, **kwargs)
        response.set_cookie('logged', self.request.user.is_authenticated())
        return response


class PublishedMixin(object):
    """Filter the queryset with the function :function:`only_published`."""

    def get_queryset(self):
        return only_published(super(PublishedMixin, self).get_queryset(), self.request)
