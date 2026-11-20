"""Tests for the django.models.mixins module."""

# pylint:disable=protected-access,unused-argument,too-few-public-methods
from __future__ import annotations

import copy
import inspect
import json
import pickle
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, override
from unittest.mock import MagicMock, patch

import numpy
import pytest
from asgiref.sync import async_to_sync
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectNotUpdated, ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import InMemoryStorage
from django.db import connection, models, transaction
from django.db.models import QuerySet, functions
from django.db.utils import IntegrityError
from django.template import Context, Template
from django.test.utils import CaptureQueriesContext

from pytoolbox import states
from pytoolbox.django import signals
from pytoolbox.django.core import exceptions
from pytoolbox.django.models import mixins
from pytoolbox.types import Missing

if TYPE_CHECKING:
    from collections.abc import Iterator

# --- Models ---------------------------------------------------------------------------------------


class _JobState(states.StateEnum):
    """A job pending, running, then ended or retried: no state transits to itself."""

    PENDING = 'PENDING'
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    TRANSITIONS = {
        PENDING: frozenset([RUNNING]),
        RUNNING: frozenset([COMPLETED, FAILED]),
        COMPLETED: frozenset(),
        FAILED: frozenset([PENDING]),
    }


class _LampState(states.StateEnum):
    """A lamp off, on, broken or lost: every state leads into BROKEN, none into OFF."""

    OFF = 'OFF'
    ON = 'ON'
    BROKEN = 'BROKEN'
    LOST = 'LOST'
    TRANSITIONS = {
        OFF: frozenset([ON, BROKEN, LOST]),
        ON: frozenset([BROKEN, LOST]),
        BROKEN: frozenset([BROKEN, LOST]),
        LOST: frozenset([BROKEN]),
    }


class _VectorField(models.Field):
    """A vector held in a numpy array, whose ``==`` compares element by element."""

    def from_db_value(self, value: str, expression: Any, db_connection: Any) -> numpy.ndarray:
        """Return the vector stored as a JSON list."""
        return numpy.array(json.loads(value))

    @override
    def get_internal_type(self) -> str:
        return 'TextField'

    @override
    def get_prep_value(self, value: Any) -> str:
        return json.dumps(numpy.asarray(value).tolist())

    @override
    def run_validators(self, value: numpy.ndarray) -> None:
        super().run_validators(value.tolist())

    @override
    def to_python(self, value: Any) -> numpy.ndarray:
        return numpy.array(value, dtype=float)

    @override
    def validate(self, value: numpy.ndarray, model_instance: models.Model) -> None:
        super().validate(value.tolist(), model_instance)


class _Attachment(mixins.BatteriesIncludedModelMixin, models.Model):
    """A row with an upload, failing validation."""

    file = models.FileField(storage=InMemoryStorage())

    objects = models.Manager()

    class Meta:
        """Meta class for test model."""

        app_label = 'test'

    @override
    def clean(self) -> None:
        """Fail the validation of every row."""
        raise ValidationError('Refused.')


class _Embedding(mixins.BatteriesIncludedModelMixin, models.Model):
    """A row holding a vector."""

    name = models.CharField(max_length=100)
    vector = _VectorField()

    objects = models.Manager()

    class Meta:
        """Meta class for test model."""

        app_label = 'test'


class _Job(mixins.BatteriesIncludedModelMixin, models.Model):
    """A row whose state follows :class:`_JobState`."""

    name = models.CharField(max_length=100)
    state = models.CharField(max_length=10)
    finished_at = models.DateTimeField(null=True, blank=True)
    states = _JobState

    objects = models.Manager()

    class Meta:
        """Meta class for test model."""

        app_label = 'test'


# [CONV-PY-ALPHA-ORDER: a proxy model follows the model it stands for]
class _FinishedJob(_Job):
    """A job stamped when it reaches a final state."""

    objects = models.Manager()

    class Meta:
        """Meta class for test model."""

        app_label = 'test'
        proxy = True

    @override
    def on_state_transition(self, previous_state: Any) -> None:
        """Stamp the job reaching a final state."""
        if self.state in _JobState.FINAL_STATES:
            self.finished_at = datetime.now(UTC)


class _Pair(mixins.BetterUniquenessErrorsMixin, models.Model):
    """A row unique by its name and note together."""

    name = models.CharField(max_length=100)
    note = models.CharField(max_length=100)

    objects = models.Manager()

    class Meta:
        """Meta class for test model."""

        app_label = 'test'
        unique_together = [('name', 'note')]


# [CONV-PY-ALPHA-ORDER: a parent model precedes its child]
class _Parent(mixins.BatteriesIncludedModelMixin, models.Model):
    """The first table of a row split over two."""

    version = models.IntegerField()

    objects = models.Manager()

    class Meta:
        """Meta class for test model."""

        app_label = 'test'


class _Child(_Parent):
    """The second table of a row split over two."""

    note = models.CharField(max_length=100)

    objects = models.Manager()

    class Meta:
        """Meta class for test model."""

        app_label = 'test'


class _Product(mixins.BatteriesIncludedModelMixin, models.Model):
    """A row unique by its brand and name, its price capped."""

    brand = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    price = models.IntegerField(default=0)
    cap = models.IntegerField(default=100)

    objects = models.Manager()

    class Meta:
        """Meta class for test model."""

        app_label = 'test'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__lte=models.F('cap')),
                name='test_product_price_capped',
            ),
            models.UniqueConstraint(fields=['brand', 'name'], name='test_product_unique_name'),
        ]


class _Reading(mixins.BatteriesIncludedModelMixin, models.Model):
    """A row whose saves write every field, its stamp included in a save limited to other fields."""

    always_update_fields = ('stamp',)
    track_update_fields = False

    value = models.IntegerField()
    note = models.CharField(max_length=100)
    stamp = models.DateTimeField(auto_now=True, null=True)
    job = models.ForeignKey(_Job, on_delete=models.PROTECT, null=True, blank=True)

    objects = models.Manager()

    class Meta:
        """Meta class for test model."""

        app_label = 'test'


# [CONV-PY-ALPHA-ORDER: a proxy model follows the model it stands for]
class _ReadingValidatedWithoutRelations(_Reading):
    """A reading validated without its relation fields."""

    objects = models.Manager()

    class Meta:
        """Meta class for test model."""

        app_label = 'test'
        proxy = True

    @override
    def get_validation_kwargs(self, update_fields: frozenset[str] | None) -> dict[str, Any]:
        """Leave every relation field out of the validation."""
        kwargs = super().get_validation_kwargs(update_fields)
        relations = [f.name for f in self.meta().concrete_fields if f.is_relation]
        return {**kwargs, 'exclude': [*kwargs.get('exclude', ()), *relations]}


class _Row(mixins.BatteriesIncludedModelMixin, models.Model):
    """A row whose saves write the fields assigned since the last one."""

    name = models.CharField(max_length=100)
    note = models.CharField(max_length=100)
    slug = models.CharField(max_length=100, blank=True)
    stamp = models.DateTimeField(auto_now=True, null=True)
    label = models.GeneratedField(
        expression=functions.Concat('name', models.Value('!')),
        output_field=models.CharField(max_length=101),
        db_persist=True,
    )

    objects = models.Manager()

    class Meta:
        """Meta class for test model."""

        app_label = 'test'

    @override
    def clean(self) -> None:
        """Derive the slug from the name."""
        self.slug = self.name.lower()


# [CONV-PY-ALPHA-ORDER: a proxy model follows the model it stands for]
class _NotedRow(_Row):
    """A row whose note is written whenever its name is."""

    objects = models.Manager()

    class Meta:
        """Meta class for test model."""

        app_label = 'test'
        proxy = True

    @override
    def get_update_fields(self, update_fields: frozenset[str] | None) -> frozenset[str] | None:
        """Write the note with the name."""
        if update_fields is not None and 'name' in update_fields:
            return update_fields | {'note'}
        return update_fields


@pytest.fixture(name='tables')
def fixture_tables() -> Iterator[None]:
    """Create the tables of the models above for one test."""
    tables = (_Attachment, _Embedding, _Job, _Parent, _Child, _Product, _Reading, _Row)
    with connection.schema_editor() as editor:
        for model in tables:
            editor.create_model(model)
    yield
    with connection.schema_editor() as editor:
        for model in reversed(tables):
            editor.delete_model(model)


@pytest.fixture(name='transitions')
def fixture_transitions() -> Iterator[list[dict[str, Any]]]:
    """Return the keywords of each state transition of a :class:`_Job` signalled during a test."""
    sent: list[dict[str, Any]] = []

    def receive(**kwargs: Any) -> None:
        sent.append(kwargs)

    signals.post_state_transition.connect(receive, sender=_Job, weak=False)
    yield sent
    signals.post_state_transition.disconnect(receive, sender=_Job)


def _get_stored(row: models.Model, *fields: str) -> tuple[Any, ...]:
    """Return the values of *fields* stored in the row of *row*."""
    return type(row).objects.values_list(*fields).get(pk=row.pk)


# --- BatteriesIncludedModelMixin: saving ----------------------------------------------------------


@pytest.mark.usefixtures('tables')
def test_a_new_instance_is_inserted() -> None:
    """A new instance with the primary key of a row fails to insert, leaving the row as it was."""
    row = _Row.objects.create(name='before', note='before')
    with pytest.raises(IntegrityError):
        _Row(name='after', note='after', pk=row.pk).save(validate=False)
    assert _get_stored(row, 'name') == ('before',)


@pytest.mark.usefixtures('tables')
def test_a_new_instance_not_forced_to_insert_updates() -> None:
    """A new instance saved with ``force_insert=False`` updates the row of its primary key."""
    row = _Row.objects.create(name='before', note='before')
    _Row(name='after', note='after', pk=row.pk).save(force_insert=False, validate=False)
    assert _get_stored(row, 'name') == ('after',)


def test_an_instance_built_without_init_takes_assignments() -> None:
    """An instance built by ``__new__`` alone, its ``__init__`` never run, takes field values."""
    row = _Row.__new__(_Row)
    row.name = 'built'
    assert row.name == 'built'


@pytest.mark.usefixtures('tables')
def test_a_save_writes_only_the_fields_assigned() -> None:
    """A field changed in the database since the instance was read survives a save of others."""
    row = _Row.objects.create(name='before', note='before')
    _Row.objects.filter(pk=row.pk).update(note='elsewhere')
    row.name = 'after'
    row.save()
    row.save()
    assert _get_stored(row, 'name', 'note') == ('after', 'elsewhere')


@pytest.mark.usefixtures('tables')
def test_a_limited_save_keeps_the_assignments_it_leaves_out() -> None:
    """A field assigned but left out of a limited save is written by the next save."""
    row = _Row.objects.create(name='before', note='before')
    row.name = 'after'
    row.note = 'after'
    row.save(update_fields=['name'])
    row.save()
    assert _get_stored(row, 'name', 'note') == ('after', 'after')


@pytest.mark.usefixtures('tables')
def test_a_save_writes_the_fields_their_pre_save_sets() -> None:
    """A field its ``pre_save`` sets, as ``auto_now`` does, is written with the fields assigned."""
    row = _Row.objects.create(name='before', note='before')
    _Row.objects.filter(pk=row.pk).update(stamp=None)
    row.name = 'after'
    row.save()
    assert _get_stored(row, 'stamp') == (row.stamp,)


@pytest.mark.usefixtures('tables')
def test_a_save_reads_the_generated_fields_back() -> None:
    """A generated field is read back by each save writing its source, and is never written."""
    row = _Row.objects.create(name='before', note='before')
    row.name = 'after'
    row.save()
    row.save()
    assert row.label == 'after!'


@pytest.mark.usefixtures('tables')
def test_a_save_leaves_the_deferred_fields_unread() -> None:
    """A save of a row read in part costs its update alone: neither saving nor validating loads."""
    row = _Row.objects.create(name='before', note='before')
    row = _Row.objects.only('name').get(pk=row.pk)
    row.name = 'after'
    with CaptureQueriesContext(connection) as queries:
        row.save()
    assert len(queries) == 1
    assert {'note', 'stamp'} <= row.get_deferred_fields()


@pytest.mark.usefixtures('tables')
def test_a_primary_key_assigned_unchanged_saves_the_row() -> None:
    """Assigning the primary key its own value updates the row."""
    row = _Row.objects.create(name='before', note='before')
    row.pk = row.pk
    row.name = 'after'
    row.save()
    assert _get_stored(row, 'name') == ('after',)


@pytest.mark.usefixtures('tables')
def test_a_new_primary_key_saves_a_copy() -> None:
    """A save of a row given a new primary key inserts a copy, the next save updating it alone."""
    row = _Row.objects.create(name='before', note='before')
    original_pk = row.pk
    row.pk = original_pk + 1
    row.save()
    assert row.previous_pk == original_pk + 1
    row.name = 'after'
    row.save()
    assert sorted(_Row.objects.values_list('pk', 'name')) == [
        (original_pk, 'before'),
        (original_pk + 1, 'after'),
    ]


@pytest.mark.usefixtures('tables')
def test_a_new_primary_key_saves_a_copy_without_tracking() -> None:
    """A save of every field, of a row given no or a new primary key, inserts a copy."""
    reading = _Reading.objects.create(note='before', value=1)
    original_pk = reading.pk
    reading.pk = None
    reading.save()
    copy_pk = reading.pk
    reading.pk = copy_pk + 1
    reading.save()
    assert sorted(_Reading.objects.values_list('pk', flat=True)) == [
        original_pk,
        copy_pk,
        copy_pk + 1,
    ]


@pytest.mark.usefixtures('tables')
def test_a_copy_tracks_its_assignments_apart() -> None:
    """A copy saved under a new primary key leaves the original's assignments to its own save."""
    row = _Row.objects.create(name='before', note='before')
    row.name = 'renamed'
    # Copying looks the model up in the app registry, where the test app is not installed.
    with patch.object(apps, 'get_model', return_value=_Row):
        clone = copy.copy(row)
    clone.pk = None
    clone.save(validate=False)
    row.save()
    assert _get_stored(row, 'name') == ('renamed',)


@pytest.mark.usefixtures('tables')
def test_a_save_without_tracking_writes_every_field() -> None:
    """With ``track_update_fields`` off, nothing is tracked and a save writes every field."""
    reading = _Reading.objects.create(note='before', value=1)
    _Reading.objects.filter(pk=reading.pk).update(note='elsewhere')
    reading.value = 2
    assert reading._assigned_fields == set()
    reading.save()
    assert _get_stored(reading, 'value', 'note') == (2, 'before')


@pytest.mark.usefixtures('tables')
def test_a_limited_save_writes_the_fields_always_updated() -> None:
    """A field listed in ``always_update_fields`` is written by a save limited to other fields."""
    reading = _Reading.objects.create(note='before', value=1)
    _Reading.objects.filter(pk=reading.pk).update(stamp=None)
    reading.value = 2
    reading.save(update_fields=['value'])
    assert _get_stored(reading, 'value', 'stamp') == (2, reading.stamp)


@pytest.mark.usefixtures('tables')
def test_update_fields_overridden_write_fields_together() -> None:
    """A field :meth:`get_update_fields` writes with another is written by a save of that one."""
    row = _NotedRow.objects.create(name='before', note='before')
    _Row.objects.filter(pk=row.pk).update(note='elsewhere')
    row.name = 'after'
    row.save()
    assert _get_stored(row, 'name', 'note') == ('after', 'before')


@pytest.mark.parametrize('load', ['refresh_from_db', 'fetch_one', 'fetch_peers'])
@pytest.mark.usefixtures('tables')
def test_a_field_read_from_the_database_is_no_assignment(load: str) -> None:
    """A field reloaded, or deferred then loaded, is left out of the next save of other fields."""
    _Row.objects.create(name='first', note='before')
    second = _Row.objects.create(name='second', note='before')

    match load:
        case 'refresh_from_db':
            row = second
            row.refresh_from_db()
        case 'fetch_one':
            row = _Row.objects.only('name').get(pk=second.pk)
        case 'fetch_peers':
            first, row = _Row.objects.only('name').fetch_mode(models.FETCH_PEERS).order_by('pk')
            assert first.note == 'before'
    assert row.note == 'before'

    _Row.objects.filter(pk=row.pk).update(note='elsewhere')
    row.name = 'after'
    row.save()
    assert _get_stored(row, 'name', 'note') == ('after', 'elsewhere')


@pytest.mark.usefixtures('tables')
def test_an_unpickled_row_tracks_its_assignments(monkeypatch: pytest.MonkeyPatch) -> None:
    """A save of a row unpickled before its model built any instance writes the fields assigned."""
    row = _Row.objects.create(name='before', note='before')
    data = pickle.dumps(row)
    monkeypatch.delattr(_Row, '_field_attnames')
    # Unpickling looks the model up in the app registry, where the test app is not installed.
    with patch.object(apps, 'get_model', return_value=_Row):
        clone = pickle.loads(data)
    clone.name = 'after'
    clone.save()
    assert _get_stored(row, 'name') == ('after',)


@pytest.mark.usefixtures('tables')
def test_a_save_of_a_row_deleted_meanwhile_fails() -> None:
    """An update is forced by default: a row deleted since it was read is not inserted again."""
    reading = _Reading.objects.create(note='before', value=1)
    _Reading.objects.filter(pk=reading.pk).delete()
    with pytest.raises(ObjectNotUpdated):
        reading.save()
    assert not _Reading.objects.exists()


@pytest.mark.usefixtures('tables')
def test_a_save_validates_the_row() -> None:
    """A row failing :meth:`full_clean` is not saved: the save fails before the database."""
    with pytest.raises(ValidationError):
        _Row(name='x' * 101, note='before').save()
    assert not _Row.objects.exists()


@pytest.mark.usefixtures('tables')
def test_a_save_validates_nothing_when_validation_is_off() -> None:
    """A save with ``validate=False`` or ``validate_on_save`` off writes an invalid row."""
    _Row(name='x' * 101, note='before').save(validate=False)
    with patch.object(_Row, 'validate_on_save', False):
        _Row(name='y' * 101, note='before').save()
    assert _Row.objects.count() == 2


@pytest.mark.usefixtures('tables')
def test_a_save_validates_without_the_deferred_fields() -> None:
    """
    A save of every field validates them all but the deferred fields and the fields
    ``validate_on_save_kwargs`` excludes, by name.
    """
    row = _Row.objects.create(name='before', note='before')
    row = _Row.objects.only('name').get(pk=row.pk)
    with (
        patch.object(_Row, 'track_update_fields', False),
        patch.object(_Row, 'validate_on_save_kwargs', {'exclude': ['name']}),
        patch.object(_Row, 'full_clean') as full_clean,
    ):
        row.save()
    full_clean.assert_called_once_with(exclude=['name', 'note', 'slug', 'stamp', 'label'])


@pytest.mark.parametrize(
    ('model', 'num_queries'),
    [(_Reading, 2), (_ReadingValidatedWithoutRelations, 1)],
)
@pytest.mark.usefixtures('tables')
def test_validation_kwargs_overridden_leave_the_relation_fields_out(
    model: type[_Reading],
    num_queries: int,
) -> None:
    """A save validating its relation fields reads the related row, one without them does not."""
    job = _Job.objects.create(name='job', state=_JobState.PENDING)
    reading = model.objects.create(note='before', value=1)
    reading.job = job
    with CaptureQueriesContext(connection) as queries:
        reading.save()
    assert len(queries) == num_queries
    assert _get_stored(reading, 'job') == (job.pk,)


@pytest.mark.usefixtures('tables')
def test_a_limited_save_validates_the_fields_it_writes() -> None:
    """A tracked save of a row holding an invalid value validates and writes the fields assigned."""
    row = _Row.objects.create(name='before', note='before')
    _Row.objects.filter(pk=row.pk).update(note='x' * 101)
    row = _Row.objects.get(pk=row.pk)
    row.name = 'after'
    row.save()
    assert _get_stored(row, 'name', 'note') == ('after', 'x' * 101)


@pytest.mark.usefixtures('tables')
def test_a_limited_save_validates_a_constraint_naming_a_field_it_writes() -> None:
    """A save writing the price checks it against the cap, a field it does not write."""
    product = _Product.objects.create(brand='acme', name='lamp', cap=10)
    product.price = 20
    with pytest.raises(ValidationError):
        product.save()
    assert _get_stored(product, 'price') == (0,)


@pytest.mark.usefixtures('tables')
def test_a_limited_save_validates_a_uniqueness_naming_a_field_it_writes() -> None:
    """A save writing the name checks it unique with the brand, a field it does not write."""
    _Product.objects.create(brand='acme', name='taken')
    product = _Product.objects.create(brand='acme', name='free')
    product.name = 'taken'
    with pytest.raises(ValidationError):
        product.save()
    assert _get_stored(product, 'name') == ('free',)


@pytest.mark.usefixtures('tables')
def test_a_save_validates_a_uniqueness_naming_a_deferred_field() -> None:
    """A save writing the name checks it unique with the brand, deferred, read for the check."""
    _Product.objects.create(brand='acme', name='taken')
    product = _Product.objects.only('name').get(
        pk=_Product.objects.create(brand='acme', name='free').pk,
    )
    product.name = 'taken'
    with pytest.raises(ValidationError):
        product.save()


@pytest.mark.usefixtures('tables')
def test_a_save_of_every_field_validates_them_all() -> None:
    """A save of every field fails on an invalid value in any of them."""
    row = _Row.objects.create(name='before', note='before')
    _Row.objects.filter(pk=row.pk).update(note='x' * 101)
    row = _Row.objects.get(pk=row.pk)
    row.name = 'after'
    with patch.object(_Row, 'track_update_fields', False), pytest.raises(ValidationError):
        row.save()
    assert _get_stored(row, 'name') == ('before',)


@pytest.mark.usefixtures('tables')
def test_a_save_writes_the_fields_clean_assigns() -> None:
    """A field the model's ``clean()`` assigns is written with the fields assigned before."""
    row = _Row.objects.create(name='Before', note='before')
    row.name = 'After'
    row.save()
    assert _get_stored(row, 'name', 'slug') == ('After', 'after')


@pytest.mark.usefixtures('tables')
def test_a_save_failing_validation_assigns_no_field() -> None:
    """A save failing validation leaves the next save to write the fields assigned alone."""
    job = _Job.objects.create(name='before', state=_JobState.FAILED)
    job.name = 'x' * 101
    with pytest.raises(ValidationError):
        job.save()
    job.name = 'after'
    job.save()
    assert _get_stored(job, 'name') == ('after',)


@pytest.mark.usefixtures('tables')
def test_a_validation_outside_a_save_assigns_no_field() -> None:
    """Validating a row before saving it leaves the save to write the fields assigned alone."""
    job = _Job.objects.create(name='before', state=_JobState.FAILED)
    job.full_clean()
    job.clean_fields()
    job.name = 'after'
    job.save()
    assert _get_stored(job, 'name') == ('after',)


@pytest.mark.usefixtures('tables')
def test_a_save_validates_a_value_compared_element_by_element() -> None:
    """A save validates a value whose ``==`` compares element by element, as a numpy array's."""
    embedding = _Embedding.objects.create(name='before', vector=[1.0, 2.0])
    embedding = _Embedding.objects.get(pk=embedding.pk)
    embedding.name = 'after'
    embedding.save()
    stored = _Embedding.objects.get(pk=embedding.pk)
    assert (stored.name, stored.vector.tolist()) == ('after', [1.0, 2.0])


def test_a_save_failing_validation_stores_no_upload() -> None:
    """A save of a row failing validation stores no upload."""
    attachment = _Attachment(file=ContentFile(b'content', name='upload.txt'))
    with pytest.raises(ValidationError):
        attachment.save()
    assert _Attachment.meta().get_field('file').storage.listdir('') == ([], [])


@pytest.mark.usefixtures('tables')
def test_an_asynchronous_save_saves_as_save_does() -> None:
    """``asave()`` forces the insert and the update, and takes the keywords ``save()`` takes."""
    row = _Row.objects.create(name='before', note='before')
    with patch.object(_Row, 'validate_on_save', False), pytest.raises(IntegrityError):
        async_to_sync(_Row(name='after', note='after', pk=row.pk).asave)()
    assert _get_stored(row, 'name') == ('before',)

    row.name = 'after'
    with pytest.raises(exceptions.DatabaseUpdatePreconditionsError):
        async_to_sync(row.asave)(pre_filters={'note': 'other'})
    assert _get_stored(row, 'name') == ('before',)

    reading = _Reading.objects.create(note='before', value=1)
    _Reading.objects.filter(pk=reading.pk).delete()
    with pytest.raises(ObjectNotUpdated):
        async_to_sync(reading.asave)()
    assert not _Reading.objects.exists()


def test_django_asave_still_runs_save() -> None:
    """
    Django's ``asave()`` still runs ``save()`` with the same four keywords: the ``asave()`` of
    :class:`~pytoolbox.django.models.mixins.BatteriesIncludedModelMixin` mirrors that
    ``sync_to_async`` wrapper.
    """
    with patch.object(models.Model, 'save') as save:
        async_to_sync(models.Model.asave)(ContentType())
    save.assert_called_once_with(
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    )
    assert list(inspect.signature(models.Model.asave).parameters) == [
        'self',
        'force_insert',
        'force_update',
        'using',
        'update_fields',
    ]


# --- BatteriesIncludedModelMixin: preconditions ---------------------------------------------------


@pytest.mark.usefixtures('tables')
def test_a_save_writes_a_row_meeting_its_preconditions() -> None:
    """A save writes a row matching all of ``pre_filters`` and none of ``pre_excludes``."""
    row = _Row.objects.create(name='before', note='before')
    row.name = 'after'
    row.save(pre_excludes={'note': 'other'}, pre_filters={'note': 'before'})
    assert _get_stored(row, 'name') == ('after',)


@pytest.mark.parametrize(
    'preconditions',
    [{'pre_excludes': {'note': 'before'}}, {'pre_filters': {'note': 'other'}}],
)
@pytest.mark.usefixtures('tables')
def test_a_save_of_a_row_failing_its_preconditions_fails(preconditions: dict) -> None:
    """A save of a row failing a precondition writes nothing, and keeps the fields to write."""
    row = _Row.objects.create(name='before', note='before')
    row.name = 'after'
    with pytest.raises(exceptions.DatabaseUpdatePreconditionsError):
        row.save(**preconditions)
    assert _get_stored(row, 'name') == ('before',)
    assert row._assigned_fields == {'name', 'slug', 'stamp'}


@pytest.mark.usefixtures('tables')
def test_a_save_with_preconditions_of_a_row_deleted_meanwhile_fails() -> None:
    """A forced update with preconditions, of a row deleted since it was read, raises."""
    reading = _Reading.objects.create(note='before', value=1)
    _Reading.objects.filter(pk=reading.pk).delete()
    with pytest.raises(exceptions.DatabaseUpdatePreconditionsError):
        reading.save(pre_filters={'note': 'before'})


@pytest.mark.usefixtures('tables')
def test_a_save_failing_its_preconditions_inserts_no_row() -> None:
    """A save failing its preconditions inserts nothing, the row deleted after its update or not."""
    reading = _Reading.objects.create(note='before', value=1)
    update = QuerySet._update

    def update_then_delete(queryset: QuerySet, *args: Any) -> Any:
        rows = update(queryset, *args)
        _Reading.objects.filter(pk=reading.pk).delete()
        return rows

    reading.value = 2
    with (
        patch.object(QuerySet, '_update', update_then_delete),
        pytest.raises(exceptions.DatabaseUpdatePreconditionsError),
    ):
        reading.save(force_update=False, pre_filters={'note': 'other'})
    assert not _Reading.objects.exists()


@pytest.mark.usefixtures('tables')
def test_a_save_of_a_row_matching_one_exclusion_fails() -> None:
    """A row matching any of ``pre_excludes`` is not written."""
    row = _Row.objects.create(name='before', note='before')
    row.name = 'after'
    with pytest.raises(exceptions.DatabaseUpdatePreconditionsError):
        row.save(pre_excludes={'note': 'before', 'slug': 'other'})
    assert _get_stored(row, 'name') == ('before',)


@pytest.mark.usefixtures('tables')
def test_a_save_of_a_row_split_over_tables_checks_its_preconditions() -> None:
    """No table of a row failing its preconditions is written, whatever table holds them."""
    child = _Child.objects.create(note='before', version=4)
    child.note = 'after'
    with pytest.raises(exceptions.DatabaseUpdatePreconditionsError):
        child.save(pre_filters={'version': 3})
    child.version = 5
    with pytest.raises(exceptions.DatabaseUpdatePreconditionsError):
        child.save(pre_filters={'note': 'other'})
    assert _get_stored(child, 'version', 'note') == (4, 'before')


@pytest.mark.usefixtures('tables')
def test_a_save_nested_in_a_save_keeps_its_preconditions() -> None:
    """A ``pre_save`` receiver saving the instance again leaves the outer update guarded."""

    def save_again(instance: _Job, **kwargs: Any) -> None:
        if instance.name != 'saved again':
            instance.name = 'saved again'
            instance.save(check_state=False, update_fields=['name'])

    job = _Job.objects.create(name='before', state=_JobState.PENDING)
    models.signals.pre_save.connect(save_again, sender=_Job, weak=False)
    try:
        job.state = _JobState.COMPLETED
        with pytest.raises(exceptions.DatabaseUpdatePreconditionsError):
            job.save()
    finally:
        models.signals.pre_save.disconnect(save_again, sender=_Job)
    assert _get_stored(job, 'state') == (_JobState.PENDING,)


@pytest.mark.usefixtures('tables')
def test_preconditions_apply_to_one_save() -> None:
    """The preconditions of an insert do not carry over to the next save."""
    row = _Row(name='before', note='before')
    row.save(pre_filters={'note': 'other'})
    row.name = 'after'
    row.save()
    assert _get_stored(row, 'name') == ('after',)


# --- BatteriesIncludedModelMixin: state machine ---------------------------------------------------


def _get_preconditions(job: _Job, **options: Any) -> mixins.Preconditions:
    """
    Return the preconditions of an update of *job* writing its state.

    The keyword arguments are those of an unguarded save, with *options* over the defaults.
    """
    return job.get_preconditions(
        frozenset(['name', 'state']),
        **{'check_state': True, 'pre_excludes': {}, 'pre_filters': {}, **options},
    )


def test_state_precondition_filters_the_states_allowed() -> None:
    """Saving a state only some states reach is guarded by those states."""
    assert _get_preconditions(_Job(state=_JobState.RUNNING)) == mixins.Preconditions(
        pre_excludes={},
        pre_filters={'state': 'PENDING'},
    )


def test_state_precondition_filters_the_states_allowed_when_most_are() -> None:
    """Saving a state most states reach is guarded by the list of those states."""
    with patch.object(_Job, 'states', _LampState):
        assert _get_preconditions(_Job(state=_LampState.LOST)) == mixins.Preconditions(
            pre_excludes={},
            pre_filters={'state__in': frozenset(['OFF', 'ON', 'BROKEN'])},
        )


def test_state_precondition_filters_the_states_declared_when_every_one_is_allowed() -> None:
    """Saving a state every state reaches, itself included, is guarded by the states declared."""
    with patch.object(_Job, 'states', _LampState):
        assert _get_preconditions(_Job(state=_LampState.BROKEN)) == mixins.Preconditions(
            pre_excludes={},
            pre_filters={'state__in': _LampState.ALL_STATES},
        )


@pytest.mark.usefixtures('tables')
def test_state_precondition_fails_an_update_into_a_state_no_transition_leads_into() -> None:
    """An update writing a state no transition leads into fails, whatever the stored state."""
    with patch.object(_Job, 'states', _LampState):
        job = _Job.objects.create(name='before', state=_LampState.OFF)
        job.state = _LampState.OFF
        with pytest.raises(exceptions.DatabaseUpdatePreconditionsError):
            job.save()


@pytest.mark.usefixtures('tables')
def test_state_precondition_refuses_a_stored_state_not_declared() -> None:
    """A row holding a state ``states`` does not declare moves into no state."""
    with patch.object(_Job, 'states', _LampState):
        job = _Job.objects.create(name='before', state=_LampState.OFF)
        _Job.objects.filter(pk=job.pk).update(state='LEGACY')
        for state in (_LampState.LOST, _LampState.BROKEN):
            job = _Job.objects.get(pk=job.pk)
            job.state = state
            with pytest.raises(exceptions.DatabaseUpdatePreconditionsError):
                job.save()
    assert _get_stored(job, 'state') == ('LEGACY',)


@pytest.mark.usefixtures('tables')
def test_state_precondition_holds_beside_the_save_exclusions() -> None:
    """A save's ``pre_excludes`` naming other fields leave the state precondition whole."""
    with patch.object(_Job, 'states', _LampState):
        job = _Job.objects.create(name='free', state=_LampState.LOST)
        job.state = _LampState.LOST
        with pytest.raises(exceptions.DatabaseUpdatePreconditionsError):
            job.save(pre_excludes={'name': 'locked'})


def test_state_precondition_left_to_the_save_naming_the_state() -> None:
    """A save whose own preconditions name the state gets no other precondition on it."""
    pre_filters = {'state__in': ['PENDING', 'RUNNING']}
    assert _get_preconditions(
        _Job(state=_JobState.RUNNING),
        pre_filters=pre_filters,
    ) == mixins.Preconditions(pre_excludes={}, pre_filters=pre_filters)


@pytest.mark.parametrize(
    ('fields', 'check_state'),
    [(frozenset(['name']), True), (frozenset(['name', 'state']), False)],
)
def test_state_precondition_skipped_for_an_update_not_checking_the_state(
    fields: frozenset[str],
    check_state: bool,
) -> None:
    """An update not writing the state, or with ``check_state`` off, gets no state precondition."""
    assert _Job(state=_JobState.RUNNING).get_preconditions(
        fields,
        check_state=check_state,
        pre_excludes={},
        pre_filters={},
    ) == mixins.Preconditions(pre_excludes={}, pre_filters={})


@pytest.mark.usefixtures('tables')
def test_state_precondition_left_out_of_a_save_without_the_state() -> None:
    """A save of other fields writes no state, and needs no transition into the current one."""
    job = _Job.objects.create(name='before', state=_JobState.RUNNING)
    job.name = 'after'
    job.save(update_fields=['name'])
    assert _get_stored(job, 'name') == ('after',)


@pytest.mark.usefixtures('tables')
def test_state_precondition_left_out_of_a_tracked_save_without_the_state() -> None:
    """A tracked save of fields other than the state needs no transition into the current one."""
    job = _Job.objects.create(name='before', state=_JobState.RUNNING)
    job.name = 'after'
    job.save()
    assert _get_stored(job, 'name') == ('after',)


@pytest.mark.usefixtures('tables')
def test_state_precondition_guards_a_tracked_save() -> None:
    """A tracked save writing a state ``states`` leads into from no state stored fails."""
    job = _Job.objects.create(name='before', state=_JobState.PENDING)
    job.state = _JobState.COMPLETED
    with pytest.raises(exceptions.DatabaseUpdatePreconditionsError):
        job.save()
    assert _get_stored(job, 'state') == (_JobState.PENDING,)


@pytest.mark.usefixtures('tables')
def test_state_precondition_guards_a_transition_from_a_state_moved_meanwhile() -> None:
    """A transition declared from the state read fails once the stored state moved."""
    job = _Job.objects.create(name='before', state=_JobState.PENDING)
    _Job.objects.filter(pk=job.pk).update(state=_JobState.RUNNING)
    job.state = _JobState.RUNNING
    with pytest.raises(exceptions.DatabaseUpdatePreconditionsError):
        job.save()


@pytest.mark.usefixtures('tables')
def test_state_precondition_skipped_by_check_state() -> None:
    """A tracked save with ``check_state`` off writes any state, as syncing an outside one does."""
    job = _Job.objects.create(name='before', state=_JobState.PENDING)
    job.check_state = False
    job.state = _JobState.COMPLETED
    job.save()
    assert _get_stored(job, 'state') == (_JobState.COMPLETED,)


@pytest.mark.usefixtures('tables')
def test_state_precondition_skipped_by_the_save() -> None:
    """A save with ``check_state=False`` writes any state."""
    job = _Job.objects.create(name='before', state=_JobState.PENDING)
    job.state = _JobState.COMPLETED
    job.save(check_state=False)
    assert _get_stored(job, 'state') == (_JobState.COMPLETED,)


@pytest.mark.usefixtures('tables')
def test_state_transition_hook_assigns_fields_its_save_writes() -> None:
    """The fields the transition hook assigns are written by the save of the transition alone."""
    job = _FinishedJob.objects.create(name='before', state=_JobState.RUNNING)
    job.state = _JobState.COMPLETED
    job.save()
    assert job.finished_at is not None
    assert _get_stored(job, 'finished_at') == (job.finished_at,)

    _Job.objects.filter(pk=job.pk).update(finished_at=None)
    job = _FinishedJob.objects.get(pk=job.pk)
    job.name = 'after'
    job.save()
    assert _get_stored(job, 'finished_at') == (None,)


@pytest.mark.usefixtures('tables')
def test_state_transition_hook_assigns_fields_a_limited_save_writes() -> None:
    """A save limited to the state writes the fields the transition hook assigns."""
    job = _FinishedJob.objects.create(name='before', state=_JobState.RUNNING)
    job = _FinishedJob.objects.get(pk=job.pk)
    job.state = _JobState.COMPLETED
    job.save(update_fields=['state'])
    assert _get_stored(job, 'state', 'finished_at') == (_JobState.COMPLETED, job.finished_at)
    assert job.finished_at is not None


@pytest.mark.usefixtures('tables')
def test_state_transition_hook_skipped_by_a_limited_save_without_the_state() -> None:
    """A new state left out of a limited save leaves the transition hook to the save writing it."""
    job = _FinishedJob.objects.create(name='before', state=_JobState.RUNNING)
    job.state = _JobState.COMPLETED
    job.name = 'after'
    job.save(update_fields=['name'])
    assert job.finished_at is None
    assert _get_stored(job, 'state', 'finished_at') == (_JobState.RUNNING, None)


@pytest.mark.usefixtures('tables')
def test_state_transition_hook_runs_on_an_insert_with_a_state() -> None:
    """An insert with a state calls the transition hook, from no previous state."""
    job = _FinishedJob.objects.create(name='before', state=_JobState.COMPLETED)
    assert job.finished_at is not None
    assert _get_stored(job, 'finished_at') == (job.finished_at,)


@pytest.mark.usefixtures('tables')
def test_a_state_transition_is_signalled(transitions: list[dict[str, Any]]) -> None:
    """A save writing a new state signals the transition, from the state it moved from."""
    job = _Job.objects.create(name='before', state=_JobState.PENDING)
    job.state = _JobState.RUNNING
    job.save()
    assert [(t['instance'], t['previous_state']) for t in transitions] == [
        (job, _JobState.PENDING),
    ]
    assert job.previous_state == _JobState.RUNNING


@pytest.mark.usefixtures('tables')
def test_a_state_transition_is_signalled_once_when_a_receiver_saves_again(
    transitions: list[dict[str, Any]],
) -> None:
    """A receiver of the transition saving the instance again signals no second transition."""

    def save_again(instance: _Job, **kwargs: Any) -> None:
        if instance.name != 'saved again':
            instance.name = 'saved again'
            instance.save(check_state=False)

    signals.post_state_transition.connect(save_again, sender=_Job, weak=False)
    try:
        with patch.object(_Job, 'track_update_fields', False):
            job = _Job.objects.create(name='before', state=_JobState.PENDING)
            job.state = _JobState.RUNNING
            job.save()
    finally:
        signals.post_state_transition.disconnect(save_again, sender=_Job)
    assert [t['previous_state'] for t in transitions] == [_JobState.PENDING]
    assert _get_stored(job, 'name') == ('saved again',)


@pytest.mark.usefixtures('tables')
def test_no_state_transition_on_a_save_leaving_the_state(transitions: list[dict[str, Any]]) -> None:
    """A save writing other fields, or the state it read, signals no transition."""
    job = _Job.objects.create(name='before', state=_JobState.FAILED)
    job.name = 'after'
    job.save()
    job.state = _JobState.FAILED
    job.save(check_state=False)
    assert transitions == []


@pytest.mark.usefixtures('tables')
def test_no_state_transition_on_a_save_without_the_state(
    transitions: list[dict[str, Any]],
) -> None:
    """A save limited to other fields signals no transition, the new state still unwritten."""
    job = _Job.objects.create(name='before', state=_JobState.PENDING)
    job.state = _JobState.RUNNING
    job.save(update_fields=['name'])
    assert transitions == []
    assert job.previous_state == _JobState.PENDING


@pytest.mark.usefixtures('tables')
def test_no_state_transition_on_an_empty_save(transitions: list[dict[str, Any]]) -> None:
    """A save writing no field, which Django skips, signals no state transition."""
    job = _Job.objects.create(name='before', state=_JobState.PENDING)
    job.state = _JobState.RUNNING
    job.save(update_fields=[])
    assert transitions == []


@pytest.mark.usefixtures('tables')
def test_a_deferred_state_stays_unread_on_load() -> None:
    """Rows loaded with their state deferred cost one query, whatever their number."""
    _Job.objects.create(name='first', state=_JobState.PENDING)
    _Job.objects.create(name='second', state=_JobState.PENDING)
    with CaptureQueriesContext(connection) as queries:
        jobs = list(_Job.objects.only('name'))
    assert len(queries) == 1
    assert all('state' in job.get_deferred_fields() for job in jobs)


@pytest.mark.usefixtures('tables')
def test_a_deferred_state_loaded_with_its_peers_is_their_previous_state() -> None:
    """A deferred state loaded for every row of a query at once is the previous state of each."""
    _Job.objects.create(name='first', state=_JobState.PENDING)
    _Job.objects.create(name='second', state=_JobState.RUNNING)
    first, second = _Job.objects.only('name').fetch_mode(models.FETCH_PEERS).order_by('pk')
    assert first.state == _JobState.PENDING
    assert (first.previous_state, second.previous_state) == (_JobState.PENDING, _JobState.RUNNING)


@pytest.mark.usefixtures('tables')
def test_a_deferred_state_read_later_is_the_previous_state(
    transitions: list[dict[str, Any]],
) -> None:
    """A deferred state is the previous state once read, and unknown before."""
    job = _Job.objects.create(name='before', state=_JobState.PENDING)
    job = _Job.objects.only('name').get(pk=job.pk)
    assert job.previous_state is Missing

    assert job.state == _JobState.PENDING
    assert job.previous_state == _JobState.PENDING

    job.state = _JobState.RUNNING
    job.save()
    assert [t['previous_state'] for t in transitions] == [_JobState.PENDING]


def test_can_transit_to_declared() -> None:
    """A transition declared in ``states`` is possible."""
    assert _Job(state=_JobState.PENDING).can_transit_to(_JobState.RUNNING) is True


def test_can_transit_to_not_declared() -> None:
    """A transition not declared in ``states`` is not possible."""
    assert _Job(state=_JobState.PENDING).can_transit_to(_JobState.COMPLETED) is False


def test_can_transit_to_raises_on_fail() -> None:
    """A transition not declared in ``states`` raises, with ``fail`` on."""
    with pytest.raises(exceptions.TransitionNotAllowedError):
        _Job(state=_JobState.PENDING).can_transit_to(_JobState.COMPLETED, fail=True)


def test_can_transit_to_noop_skip() -> None:
    """A transition to the current state is skipped with ``noop_skip`` on, even with ``fail`` on."""
    job = _Job(state=_JobState.PENDING)
    assert job.can_transit_to(_JobState.PENDING, fail=True, noop_skip=True) is False


def test_check_state_in_valid() -> None:
    """A current state among those given is found."""
    assert _Job(state=_JobState.PENDING).check_state_in(['PENDING', 'RUNNING']) is True


def test_check_state_in_invalid() -> None:
    """A current state out of those given is not found."""
    assert _Job(state=_JobState.PENDING).check_state_in(['COMPLETED']) is False


def test_check_state_in_raises_on_fail() -> None:
    """A current state out of those given raises, with ``fail`` on."""
    with pytest.raises(exceptions.InvalidStateError):
        _Job(state=_JobState.PENDING).check_state_in(['COMPLETED'], fail=True)


# --- BatteriesIncludedModelMixin: accessors -------------------------------------------------------


def test_a_template_reads_the_options() -> None:
    """A template reads the model's options, which their name ``_meta`` hides from it."""
    rendered = Template('{{ row.meta.verbose_name }}').render(Context({'row': _Row()}))
    assert rendered == _Row._meta.verbose_name  # pylint:disable=no-member


def test_a_related_model_and_its_manager_are_found_through_the_field() -> None:
    """The model a foreign key leads to, and its default manager, are found by the key's name."""
    assert _Reading.get_related_model('job') is _Job
    assert _Reading.get_related_manager('job') is _Job._default_manager


@pytest.mark.usefixtures('tables')
def test_reload_reads_the_row_again() -> None:
    """A reload holds the stored values, in a new instance."""
    row = _Row.objects.create(name='before', note='before')
    _Row.objects.filter(pk=row.pk).update(name='elsewhere')
    reloaded = row.reload()
    assert reloaded is not row
    assert (reloaded.name, row.name) == ('elsewhere', 'before')


# --- BetterUniquenessErrorsMixin ------------------------------------------------------------------


@pytest.mark.usefixtures('tables')
def test_uniqueness_error_leaves_the_transaction_usable() -> None:
    """A duplicate turned into a validation error leaves the outer transaction usable."""
    duplicate = IntegrityError(
        'duplicate key value violates unique constraint "pair"\n'
        'DETAIL:  Key (name, note)=(a, b) already exists.'
    )
    with transaction.atomic():
        with (
            patch.object(_Pair, '_do_insert', side_effect=duplicate),
            pytest.raises(ValidationError),
        ):
            _Pair(name='a', note='b').save()
        assert not _Row.objects.exists()


def test_uniqueness_save_converts_integrity_error() -> None:
    """IntegrityError with duplicate key is converted to ValidationError."""

    class Base:
        """Test class."""

        _state = MagicMock(db=None)

        def save(self, *args, **kwargs):
            """Test method."""
            raise IntegrityError(
                'duplicate key value violates unique (name)',
            )

    class TestObj(mixins.BetterUniquenessErrorsMixin, Base):
        """Test object with BetterUniquenessErrorsMixin."""

    obj = TestObj()
    obj._meta = MagicMock()
    obj._meta.unique_together = [('name',)]
    obj.unique_from_integrity_error = True
    obj.unique_together_hide_fields = ()
    mock_error = ValidationError('unique error')
    obj.unique_error_message = MagicMock(return_value=mock_error)

    with pytest.raises(ValidationError):
        obj.save()


def test_uniqueness_save_reraises_non_matching_integrity() -> None:
    """IntegrityError without duplicate key pattern is re-raised as-is."""

    class Base:
        """Test class."""

        _state = MagicMock(db=None)

        def save(self, *args, **kwargs):
            """Test method."""
            raise IntegrityError('some other error')

    class TestObj(mixins.BetterUniquenessErrorsMixin, Base):
        """Test object with BetterUniquenessErrorsMixin."""

    obj = TestObj()
    obj.unique_from_integrity_error = True
    obj.unique_together_hide_fields = ()

    with pytest.raises(IntegrityError, match='some other error'):
        obj.save()


def test_uniqueness_save_disabled() -> None:
    """When unique_from_integrity_error is False, IntegrityError is raised."""

    class Base:
        """Test class."""

        _state = MagicMock(db=None)

        def save(self, *args, **kwargs):
            """Test method."""
            raise IntegrityError('duplicate key value (name, org)')

    class TestObj(mixins.BetterUniquenessErrorsMixin, Base):
        """Test object with BetterUniquenessErrorsMixin."""

    obj = TestObj()
    obj.unique_from_integrity_error = False
    obj.unique_together_hide_fields = ()

    with pytest.raises(IntegrityError):
        obj.save()


def test_uniqueness_hidden_fields_calls_handler() -> None:
    """When all fields are hidden, _handle_hidden_duplicate_key_error is called."""

    class Base:
        """Test class."""

        _state = MagicMock(db=None)

        def save(self, *args, **kwargs):
            """Test method."""
            raise IntegrityError('duplicate key value (org)')

    class TestObj(mixins.BetterUniquenessErrorsMixin, Base):
        """Test object with BetterUniquenessErrorsMixin."""

    obj = TestObj()
    obj._meta = MagicMock()
    obj._meta.unique_together = [('org',)]
    obj.unique_from_integrity_error = True
    obj.unique_together_hide_fields = ('org',)
    obj._handle_hidden_duplicate_key_error = MagicMock()
    obj.save()
    obj._handle_hidden_duplicate_key_error.assert_called_once()


def test_perform_unique_checks_hides_fields() -> None:
    """_perform_unique_checks filters hidden fields from error messages."""
    error = MagicMock()
    error.params = {'unique_check': ['org', 'name']}

    class Base:
        """Test class."""

        def _perform_unique_checks(self, unique_checks):  # pylint:disable=unused-argument
            return {'__all__': [error]}

    class TestObj(mixins.BetterUniquenessErrorsMixin, Base):
        """Test object with BetterUniquenessErrorsMixin."""

    obj = TestObj()
    obj.unique_together_hide_fields = ('org',)
    obj.unique_error_message = MagicMock(return_value=MagicMock())

    result = obj._perform_unique_checks([])
    # Error should be remapped to the remaining field 'name'
    assert 'name' in result
    obj.unique_error_message.assert_called_once()


def test_perform_unique_checks_no_hidden() -> None:
    """Without hidden fields, _perform_unique_checks returns errors as-is."""
    error = MagicMock()
    error.params = {'unique_check': ['name']}

    class Base:
        """Test class."""

        def _perform_unique_checks(self, unique_checks):
            return {'name': [error]}

    class TestObj(mixins.BetterUniquenessErrorsMixin, Base):
        """Test object with BetterUniquenessErrorsMixin."""

    obj = TestObj()
    obj.unique_together_hide_fields = ()
    result = obj._perform_unique_checks([])
    assert result == {'name': [error]}


def test_perform_unique_checks_single_field_error_passthrough() -> None:
    """Single-field unique check errors pass through even with hidden set."""
    error = MagicMock()
    error.params = {'unique_check': ['name']}

    class Base:
        """Test class."""

        def _perform_unique_checks(self, unique_checks):
            return {'name': [error]}

    class TestObj(mixins.BetterUniquenessErrorsMixin, Base):
        """Test object with BetterUniquenessErrorsMixin."""

    obj = TestObj()
    obj.unique_together_hide_fields = ('org',)
    result = obj._perform_unique_checks([])
    assert 'name' in result
    assert error in result['name']


# --- Keywords passed on ---------------------------------------------------------------------------


class _SaveRecorder:
    """The next class of a save chain: records what reaches it, with what the mixins read."""

    _meta = MagicMock(
        concrete_fields=[],
        fields=[],
        local_concrete_fields=[],
        pk=MagicMock(attname='id'),
    )
    full_clean = MagicMock()
    pk = 1

    def __init__(self) -> None:
        self._state = MagicMock(adding=False, db=None)
        self.saved: dict = {}

    def get_constraints(self) -> list:
        """Return no constraint."""
        return []

    def get_deferred_fields(self) -> set[str]:
        """Return no deferred field."""
        return set()

    def save(self, **kwargs) -> None:
        """Record the keywords received."""
        self.saved = kwargs

    def _get_unique_checks(self, **kwargs) -> tuple[list, list]:
        """Return no uniqueness check."""
        return [], []


@pytest.mark.parametrize(
    'mixin',
    [mixins.BatteriesIncludedModelMixin, mixins.BetterUniquenessErrorsMixin],
)
def test_a_save_mixin_passes_on_the_keywords_it_does_not_take(mixin: type) -> None:
    """A keyword the mixin does not take reaches the next save in the chain."""
    row = type('Row', (mixin, _SaveRecorder), {})()
    row.save(update_fields=['name'], marker=True)
    assert row.saved['marker'] is True
