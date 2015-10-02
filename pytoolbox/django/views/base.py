# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2015 David Fischer. All rights reserved.
#  Origin         : https://github.com/davidfischer-ch/pytoolbox.git
#
#**********************************************************************************************************************#

from __future__ import absolute_import, division, print_function, unicode_literals

"""
Extra views.
"""

from django.http import HttpResponseRedirect
from django.views.generic.edit import DeleteView


class CancellableDeleteView(DeleteView):
    """Handle the cancel action (detect a cancel parameter in the POST request)."""

    def post(self, request, *args, **kwargs):
        if 'cancel' in request.POST:
            return HttpResponseRedirect(self.success_url)
        return super(CancellableDeleteView, self).post(request, *args, **kwargs)
