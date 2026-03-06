# pylint:disable=unused-argument
from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError

from pytoolbox.django.forms import mixins as forms_mixins
from pytoolbox.django.views import mixins


# ---------------------------------------------------------------------------
# AddRequestToFormKwargsMixin
# ---------------------------------------------------------------------------

def test_add_request_to_form_kwargs() -> None:
    """Request is added to form kwargs when form is a RequestMixin."""
    class Base:
        def get_form_kwargs(self, *args, **kwargs):
            return {'initial': {}}

        def get_form_class(self):
            class MyForm(forms_mixins.RequestMixin):
                pass
            return MyForm

    class View(mixins.AddRequestToFormKwargsMixin, Base):
        request = MagicMock()

    view = View()
    kwargs = view.get_form_kwargs()
    assert 'request' in kwargs
    assert kwargs['request'] is view.request


def test_add_request_not_added_for_plain_form() -> None:
    """Request is not added when form is not a RequestMixin subclass."""
    class PlainForm:
        pass

    class Base:
        def get_form_kwargs(self, *args, **kwargs):
            return {'initial': {}}

        def get_form_class(self):
            return PlainForm

    class View(mixins.AddRequestToFormKwargsMixin, Base):
        request = MagicMock()

    view = View()
    kwargs = view.get_form_kwargs()
    assert 'request' not in kwargs


# ---------------------------------------------------------------------------
# BaseModelMultipleMixin
# ---------------------------------------------------------------------------

def test_base_model_multiple_context_name_explicit() -> None:
    """Explicit context_object_name is returned as-is."""
    class View(mixins.BaseModelMultipleMixin):
        context_object_name = 'articles'

    view = View()
    assert view.get_context_object_name([]) == 'articles'


def test_base_model_multiple_context_name_from_model() -> None:
    """Derives context name from the base model's model_name."""
    instance_list = MagicMock()
    instance_list.model._meta.proxy_for_model = None
    instance_list.model._meta.model._meta.model_name = 'article'

    class View(mixins.BaseModelMultipleMixin):
        context_object_name = None

    view = View()
    result = view.get_context_object_name(instance_list)
    assert result == 'article_list'


# ---------------------------------------------------------------------------
# BaseModelSingleMixin
# ---------------------------------------------------------------------------

def test_base_model_single_context_name_explicit() -> None:
    """Explicit context_object_name is returned as-is."""
    class View(mixins.BaseModelSingleMixin):
        context_object_name = 'article'

    view = View()
    assert view.get_context_object_name(MagicMock()) == 'article'


def test_base_model_single_context_name_from_instance() -> None:
    """Derives context name from the model instance's base model name."""
    from django.db import models

    class FakeModel(models.Model):
        class Meta:
            app_label = 'test'

    instance = FakeModel.__new__(FakeModel)

    class View(mixins.BaseModelSingleMixin):
        context_object_name = None

    view = View()
    result = view.get_context_object_name(instance)
    assert result == 'fakemodel'


# ---------------------------------------------------------------------------
# InitialMixin
# ---------------------------------------------------------------------------

def test_initial_mixin_get_initial() -> None:
    """get_initial populates values from query string via initials map."""
    class Base:
        def get_initial(self):
            return {}

    class View(mixins.InitialMixin, Base):
        initials = {'name': 'default_name', 'age': 25}

    view = View()
    view.request = MagicMock()
    view.request.GET = {'name': 'Alice'}
    result = view.get_initial()
    assert result['name'] == 'Alice'
    assert result['age'] == 25


def test_set_initial_from_func_success() -> None:
    """set_initial_from_func applies func to the query param value."""
    class View(mixins.InitialMixin):
        pass

    view = View()
    view.request = MagicMock()
    view.request.GET = {'count': '42'}
    initial = {}
    result = view.set_initial_from_func(
        initial, 'count', None, int, 'bad value', 'missing')
    assert result == 42
    assert initial['count'] == 42


def test_set_initial_from_func_value_error() -> None:
    """set_initial_from_func returns None and adds error on ValueError."""
    class View(mixins.InitialMixin):
        pass

    view = View()
    view.request = MagicMock()
    view.request.GET = {'count': 'abc'}
    initial = {}
    result = view.set_initial_from_func(
        initial, 'count', None, int, 'bad value', 'missing')
    assert result is None


def test_set_initial_from_func_key_error() -> None:
    """set_initial_from_func returns None and adds error on KeyError."""
    class View(mixins.InitialMixin):
        pass

    def bad_func(val):
        raise KeyError('no such key')

    view = View()
    view.request = MagicMock()
    view.request.GET = {'key': 'val'}
    initial = {}
    result = view.set_initial_from_func(
        initial, 'key', None, bad_func, 'bad', 'missing')
    assert result is None


def test_set_initial_from_func_default() -> None:
    """set_initial_from_func uses default when key is not in GET."""
    class View(mixins.InitialMixin):
        pass

    sentinel = object()
    view = View()
    view.request = MagicMock()
    # Use MagicMock for GET so .get can be controlled
    mock_get = MagicMock()
    mock_get.get.return_value = sentinel
    view.request.GET = mock_get
    initial = {}
    result = view.set_initial_from_func(
        initial, 'key', sentinel, int, 'bad', 'missing')
    assert result is sentinel
    assert initial['key'] is sentinel


def test_set_initial_from_model_success() -> None:
    """set_initial_from_model looks up instance by pk from query string."""
    class View(mixins.InitialMixin):
        pass

    view = View()
    view.request = MagicMock()
    view.request.GET = {'author': '5'}
    model = MagicMock()
    expected = MagicMock()
    model.objects.for_user.return_value.get.return_value = expected

    initial = {}
    result = view.set_initial_from_model(
        initial, 'author', None, model, 'bad', 'missing')
    assert result is expected
    assert initial['author'] is expected


def test_set_initial_from_model_value_error() -> None:
    """set_initial_from_model returns None on ValueError from pk lookup."""
    class View(mixins.InitialMixin):
        pass

    view = View()
    view.request = MagicMock()
    view.request.GET = {'author': 'bad'}
    model = MagicMock()
    model.objects.for_user.return_value.get.side_effect = ValueError

    initial = {}
    result = view.set_initial_from_model(
        initial, 'author', None, model, 'bad value', 'missing')
    assert result is None


def test_set_initial_from_model_does_not_exist() -> None:
    """set_initial_from_model returns None when model instance not found."""
    class View(mixins.InitialMixin):
        pass

    view = View()
    view.request = MagicMock()
    view.request.GET = {'author': '999'}
    model = MagicMock()
    model.DoesNotExist = type('DoesNotExist', (Exception,), {})
    model.objects.for_user.return_value.get.side_effect = (
        model.DoesNotExist)

    initial = {}
    result = view.set_initial_from_model(
        initial, 'author', None, model, 'bad', 'not found')
    assert result is None


# ---------------------------------------------------------------------------
# LoggedCookieMixin
# ---------------------------------------------------------------------------

def test_logged_cookie_mixin_authenticated() -> None:
    """Sets logged cookie to True for authenticated users."""
    class Base:
        def post(self, *args, **kwargs):
            return MagicMock()

    class View(mixins.LoggedCookieMixin, Base):
        request = MagicMock()

    view = View()
    view.request.user.is_authenticated = True
    response = view.post()
    response.set_cookie.assert_called_once_with('logged', True)


def test_logged_cookie_mixin_unauthenticated() -> None:
    """Sets logged cookie to False for unauthenticated users."""
    class Base:
        def post(self, *args, **kwargs):
            return MagicMock()

    class View(mixins.LoggedCookieMixin, Base):
        request = MagicMock()

    view = View()
    view.request.user.is_authenticated = False
    response = view.post()
    response.set_cookie.assert_called_once_with('logged', False)


# ---------------------------------------------------------------------------
# RedirectMixin
# ---------------------------------------------------------------------------

def test_redirect_mixin_redirects() -> None:
    """dispatch() redirects when redirect_view is set."""
    class Base:
        def dispatch(self, request, *args, **kwargs):
            return 'original'

    class View(mixins.RedirectMixin, Base):
        redirect_view = 'home'

    view = View()
    with patch(
        'pytoolbox.django.views.mixins.redirect',
        return_value='redirected'
    ) as mock_redirect:
        result = view.dispatch(MagicMock())
        mock_redirect.assert_called_once_with('home')
        assert result == 'redirected'


def test_redirect_mixin_no_redirect() -> None:
    """dispatch() proceeds normally when redirect_view is None."""
    class Base:
        def dispatch(self, request, *args, **kwargs):
            return 'original'

    class View(mixins.RedirectMixin, Base):
        redirect_view = None

    view = View()
    result = view.dispatch(MagicMock())
    assert result == 'original'


# ---------------------------------------------------------------------------
# TemplateResponseMixin
# ---------------------------------------------------------------------------

def test_template_response_mixin_explicit_name() -> None:
    """Returns template_name when explicitly set."""
    class View(mixins.TemplateResponseMixin):
        template_name = 'custom.html'

    view = View()
    assert view.get_template_names() == ['custom.html']


def test_template_response_mixin_auto_names() -> None:
    """Generates template candidates from directory and action."""
    class View(mixins.TemplateResponseMixin):
        template_name = None
        template_directory = 'articles'
        action = 'detail'

    view = View()
    names = view.get_template_names()
    assert names == [
        'articles/detail.html',
        'default/detail.html'
    ]


# ---------------------------------------------------------------------------
# ValidationErrorsMixin
# ---------------------------------------------------------------------------

def test_validation_errors_mixin_catches_field_error() -> None:
    """form_valid catches ValidationError and adds field errors to form."""
    class Base:
        def form_valid(self, form):
            raise ValidationError({'name': 'Name is required'})

        def form_invalid(self, form):
            return 'invalid_response'

    class View(mixins.ValidationErrorsMixin, Base):
        pass

    view = View()
    form = MagicMock()
    result = view.form_valid(form)
    form.add_error.assert_called()
    assert result == 'invalid_response'


def test_validation_errors_mixin_catches_non_field_error() -> None:
    """form_valid adds non-field errors to NON_FIELD_ERRORS."""
    class Base:
        def form_valid(self, form):
            raise ValidationError('General error')

        def form_invalid(self, form):
            return 'invalid_response'

    class View(mixins.ValidationErrorsMixin, Base):
        pass

    view = View()
    form = MagicMock()
    result = view.form_valid(form)
    # Non-field errors go through _handle_unknown_error
    form.add_error.assert_called()
    assert result == 'invalid_response'


def test_validation_errors_mixin_success() -> None:
    """form_valid returns normally when no ValidationError is raised."""
    class Base:
        def form_valid(self, form):
            return 'success'

    class View(mixins.ValidationErrorsMixin, Base):
        pass

    view = View()
    form = MagicMock()
    result = view.form_valid(form)
    assert result == 'success'
