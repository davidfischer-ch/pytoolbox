from __future__ import annotations

from pytoolbox import states


class MediaState(states.StateEnum):

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


class PlayerState(states.StateEnum):

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


class MergeState(MediaState, PlayerState, metaclass=states.StateEnumMergeMetaclass):
    """This class is used only for testing: Its not engineered for brewing coffee!"""


def test_state_enum_get() -> None:
    assert MediaState.get('new') == MediaState.NEW
    assert MediaState.get('New') is None
    assert MediaState.get('all') == MediaState.ALL_STATES
    assert MediaState.get('other') is None


def test_state_enum_get_transit_from() -> None:
    assert MediaState.get_transit_from(MediaState.NEW) == frozenset([MediaState.NEW])
    assert MediaState.get_transit_from(MediaState.ANALYZING) == frozenset([
        MediaState.QUEUED_ANALYZE
    ])
    assert MediaState.get_transit_from(MediaState.DELETED, auto_inverse=True) == (
        frozenset([MediaState.NEW, MediaState.REJECTED, MediaState.DELETED]),
        False
    )
    assert MediaState.get_transit_from(MediaState.REPAIRING, auto_inverse=True) == (
        frozenset([MediaState.ANALYZING]),
        True
    )


def test_state_enum_all_states() -> None:
    assert MediaState.ALL_STATES == frozenset([
        MediaState.NEW,
        MediaState.QUEUED_ANALYZE,
        MediaState.ANALYZING,
        MediaState.REPAIRING,
        MediaState.REJECTED,
        MediaState.READY,
        MediaState.DELETED
    ])


def test_state_enum_final_states() -> None:
    assert MediaState.FINAL_STATES == frozenset([MediaState.DELETED, MediaState.REJECTED])


def test_merged_state_get() -> None:
    assert MergeState.get('stopped') == MergeState.STOPPED
    assert MergeState.get('stopPed') is None
    assert MergeState.get('all') == MergeState.ALL_STATES
    assert MergeState.get('other') is None


def test_merged_state_get_transit_from() -> None:
    assert MergeState.get_transit_from(MergeState.NEW) == frozenset([MergeState.NEW])
    assert MergeState.get_transit_from(MergeState.PLAYING) == frozenset([MergeState.STOPPED])
    assert MergeState.get_transit_from(MergeState.DELETED, auto_inverse=True) == (
        frozenset([MergeState.NEW, MergeState.REJECTED, MergeState.DELETED]),
        False
    )
    assert MergeState.get_transit_from(MergeState.STOPPED, auto_inverse=True) == (
        frozenset([MergeState.NEW, MergeState.PLAYING]),
        True
    )


def test_merged_state_all_states() -> None:
    assert MergeState.ALL_STATES == frozenset([
        MergeState.NEW,
        MergeState.QUEUED_ANALYZE,
        MergeState.ANALYZING,
        MergeState.REPAIRING,
        MergeState.REJECTED,
        MergeState.READY,
        MergeState.DELETED,
        MergeState.STOPPED,
        MergeState.PLAYING
    ])


def test_merged_state_final_states() -> None:
    assert MergeState.FINAL_STATES == frozenset([MergeState.DELETED, MergeState.REJECTED])
