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

import six, unittest
from pytoolbox import states
from pytoolbox.unittest import FilterByTagsMixin


class MediaState(six.with_metaclass(states.StateEnumMetaclass, states.StateEnum)):

    NEW = 'NEW'
    QUEUED_ANALYZE = 'QUEUED_ANALYZE'
    ANALYZING = 'ANALYZING'
    REPAIRING = 'REPAIRING'
    REJECTED = 'REJECTED'
    READY = 'READY'
    DELETED = 'DELETED'

    PROCESSABLE_STATES = frozenset([READY])
    RUNNING_STATES = frozenset([ANALYZING, REPAIRING])
    WITH_FILE_STATES = frozenset([READY])
    WITHOUT_FILE_STATES = frozenset([REJECTED])

    TRANSITIONS = {
        NEW: frozenset([NEW, QUEUED_ANALYZE]),
        QUEUED_ANALYZE: frozenset([ANALYZING, REJECTED, DELETED]),
        ANALYZING: frozenset([REPAIRING, REJECTED, READY, DELETED]),
        REPAIRING: frozenset([REJECTED, READY, DELETED]),
        REJECTED: frozenset([]),
        READY: frozenset([DELETED]),
        DELETED: frozenset([])
    }

    OTHER = 10


class PlayState(six.with_metaclass(states.StateEnumMetaclass, states.StateEnum)):

    NEW = 'NEW'
    STOPPED = 'STOPPED'
    PLAYING = 'PLAYING'
    DELETED = 'DELETED'

    PROCESSABLE_STATES = frozenset(['STOPPED', 'PLAYING'])
    RUNNING_STATES = frozenset(['PLAYING'])
    WITH_FILE_STATES = frozenset(['STOPPED', 'PLAYING'])
    WITHOUT_FILE_STATES = frozenset(['DELETED'])

    TRANSITIONS = {
        NEW: frozenset([NEW, STOPPED]),
        STOPPED: frozenset([PLAYING, DELETED]),
        PLAYING: frozenset([STOPPED, DELETED]),
        DELETED: frozenset([])
    }


class MergeState(six.with_metaclass(states.StateEnumMergeMetaclass, MediaState, PlayState)):
    """This class is used only for testing: Its not engineered for brewing coffee!"""
    pass


class TestStateEnumWithMetaclass(FilterByTagsMixin, unittest.TestCase):

    tags = ('states', )

    def test_get(self):
        self.assertEqual(MediaState.get('new'), MediaState.NEW)
        self.assertIsNone(MediaState.get('New'))
        self.assertEqual(MediaState.get('all'), MediaState.ALL_STATES)
        self.assertIsNone(MediaState.get('other'))

    def test_get_transit_from(self):
        self.assertEqual(MediaState.get_transit_from(MediaState.NEW), frozenset([MediaState.NEW]))
        self.assertEqual(MediaState.get_transit_from(MediaState.ANALYZING), frozenset([MediaState.QUEUED_ANALYZE]))
        self.assertEqual(MediaState.get_transit_from(MediaState.DELETED, auto_inverse=True), (
            frozenset([MediaState.NEW, MediaState.REJECTED, MediaState.DELETED]), False
        ))
        self.assertEqual(MediaState.get_transit_from(MediaState.REPAIRING, auto_inverse=True), (
            frozenset([MediaState.ANALYZING]), True
        ))

    def test_ALL_STATES(self):
        self.assertEqual(MediaState.ALL_STATES, frozenset([
            MediaState.NEW, MediaState.QUEUED_ANALYZE, MediaState.ANALYZING, MediaState.REPAIRING, MediaState.REJECTED,
            MediaState.READY, MediaState.DELETED
        ]))

    def test_FINAL_STATES(self):
        self.assertEqual(MediaState.FINAL_STATES, frozenset([MediaState.DELETED, MediaState.REJECTED]))


class TestStateEnumMergeWithMetaclass(FilterByTagsMixin, unittest.TestCase):

    tags = ('states', )

    def test_get(self):
        self.assertEqual(MergeState.get('stopped'), MergeState.STOPPED)
        self.assertIsNone(MergeState.get('stopPed'))
        self.assertEqual(MergeState.get('all'), MergeState.ALL_STATES)
        self.assertIsNone(MergeState.get('other'))

    def test_get_transit_from(self):
        self.assertEqual(MergeState.get_transit_from(MergeState.NEW), frozenset([MergeState.NEW]))
        self.assertEqual(MergeState.get_transit_from(MergeState.PLAYING), frozenset([MergeState.STOPPED]))
        self.assertEqual(MergeState.get_transit_from(MergeState.DELETED, auto_inverse=True), (
            frozenset([MergeState.NEW, MergeState.REJECTED, MergeState.DELETED]), False
        ))
        self.assertEqual(MergeState.get_transit_from(MergeState.STOPPED, auto_inverse=True), (
            frozenset([MergeState.NEW, MergeState.PLAYING]), True
        ))

    def test_ALL_STATES(self):
        self.assertEqual(MergeState.ALL_STATES, frozenset([
            MergeState.NEW, MergeState.QUEUED_ANALYZE, MergeState.ANALYZING, MergeState.REPAIRING, MergeState.REJECTED,
            MergeState.READY, MergeState.DELETED, MergeState.STOPPED, MergeState.PLAYING
        ]))

    def test_FINAL_STATES(self):
        self.assertEqual(MergeState.FINAL_STATES, frozenset([
            MergeState.DELETED, MergeState.REJECTED
        ]))
