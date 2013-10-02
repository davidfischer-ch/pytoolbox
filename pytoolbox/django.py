# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                       PYUTILS - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
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

from __future__ import absolute_import

from django.contrib.gis.geos import Point
from django.contrib.gis.maps.google import GEvent, GIcon, GMarker
from django.core.urlresolvers import reverse
from django.forms import ModelForm, widgets
from django.forms.util import ErrorList
from django.http import HttpResponseRedirect
from django.utils.html import mark_safe
from django.utils.translation import ugettext as _
from django.views.generic.edit import DeleteView
from os.path import join


# Models ---------------------------------------------------------------------------------------------------------------

class SmartModelMixin(object):

    # https://docs.djangoproject.com/en/dev/topics/class-based-views/generic-editing/
    def get_absolute_url(self):
        return reverse(u'{0}_{1}'.format(self.__class__.__name__.lower(), u'update' if self.pk else u'create'),
                       kwargs={u'pk': self.pk} if self.pk else None)


class GoogleMapMixin(object):

    map_icon_varname_field = u'category'
    map_marker_title_field = u'title'
    map_marker_title_field_default = u'New thing'

    def map_icon(self, icons_url=u'/static/markers/', size=(24, 24)):
        varname = getattr(self, self.map_icon_varname_field)
        if varname:
            return GIcon(varname, image=join(icons_url, varname.lower() + u'.png'), iconsize=size)
        return None

    def map_marker(self, default_location=Point(6.146805, 46.227574), draggable=False, form_update=False,
                   highlight_class=None, dbclick_edit=False, **kwargs):
        title = unicode(getattr(self, self.map_marker_title_field)) or self.map_marker_title_field_default
        marker = GMarker(self.location or default_location, title=_(title).encode('ascii', 'xmlcharrefreplace'),
                         draggable=draggable, icon=self.map_icon(**kwargs))
        events = []
        if form_update:
            events.append(GEvent(u'mouseup',
                          u"function() { $('#id_location').val('POINT ('+this.xa.x+' '+this.xa.y+')'); }"))
        if highlight_class:
            events.append(GEvent(u'mouseover', u"function() {{ $('#marker_{0}').addClass('{1}'); }}".format(
                          self.id, highlight_class)))
            events.append(GEvent(u'mouseout', u"function() {{ $('#marker_{0}').removeClass('{1}'); }}".format(
                          self.id, highlight_class)))
        if dbclick_edit:
            events.append(GEvent(u'dblclick', u"function() {{ window.location = '{0}'; }}".format(
                          self.get_absolute_url())))
        [marker.add_event(event) for event in events]
        return marker

# Forms ----------------------------------------------------------------------------------------------------------------

class SmartModelForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(SmartModelForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, widgets.DateInput):
                field.widget = CalendarDateInput()
                field.widget.attrs[u'class'] = u'dateinput input-small'
            if isinstance(field.widget, widgets.TimeInput):
                field.widget = ClockTimeInput()
                field.widget.attrs[u'class'] = u'timeinput input-small'
        try:
            self._meta.model.init_form(self)
        except AttributeError:
            pass

    def clean(self):
        super(SmartModelForm, self).clean()
        try:
            return self._meta.model.clean_form(self)
        except AttributeError:
            return self.cleaned_data


class CalendarDateInput(widgets.DateInput):
    def render(self, *args, **kwargs):
        html = super(CalendarDateInput, self).render(*args, **kwargs)
        return mark_safe(u'<div class="input-append date">{0}'
                         '<span class="add-on"><i class="icon-calendar"></i></span></div>'.format(html))


class ClockTimeInput(widgets.TimeInput):
    def render(self, *args, **kwargs):
        html = super(ClockTimeInput, self).render(*args, **kwargs)
        return mark_safe(u'<div class="input-append bootstrap-timepicker">{0}'
                         '<span class="add-on"><i class="icon-time"></i></span></div>'.format(html))


def conditional_required(form, required_dict, cleanup=False):
    data = form.cleaned_data
    for name, value in data.items():
        required = required_dict.get(name, None)
        if required and not value:
            form._errors[name] = ErrorList([u'This field is required.'])
        if required is False and cleanup:
            data[name] = None
    return data

# Views ----------------------------------------------------------------------------------------------------------------

class SmartDeleteView(DeleteView):

    def post(self, request, *args, **kwargs):
        if u'cancel' in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)
        return super(SmartDeleteView, self).post(request, *args, **kwargs)


def set_disabled(form, field_name, value=False):
    if value:
        form.fields[field_name].widget.attrs[u'disabled'] = True
    else:
        try:
            del form.fields[field_name].widget.attrs[u'disabled']
        except:
            pass
