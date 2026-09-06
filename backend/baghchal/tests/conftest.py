"""
Pytest async and Django configuration for backend tests.
"""

from __future__ import annotations

import asyncio
from typing import Generator
from unittest.mock import patch

import django
from django.conf import settings

import pytest


def _make_test_settings():
    return dict(
        DEBUG=True,
        SECRET_KEY="test-secret-key-for-backend-tests",
        INSTALLED_APPS=[
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "core",
            "baghchal",
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                # Shared-cache in-memory DB so every thread (including the
                # worker threads asgiref uses for sync ORM calls) sees the
                # same migrated schema instead of a fresh empty database.
                "NAME": "file::memory:?cache=shared&mode=memory&uri=true",
            }
        },
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        AUTH_USER_MODEL="core.User",  # match production so JWT/guest flows use the real model
        ROOT_URLCONF="backend.urls",
        USE_TZ=True,
        ALLOWED_HOSTS=["testserver"],
        SILENCED_SYSTEM_CHECKS=[
            "admin.E403",
            "admin.E404",
            "admin.E408",
            "admin.E409",
            "admin.E410",
            "admin.W411",
            "fields.E304",
        ],
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [],
                "APP_DIRS": True,
                "OPTIONS": {
                    "context_processors": [
                        "django.contrib.auth.context_processors.auth",
                        "django.contrib.messages.context_processors.messages",
                    ],
                },
            },
        ],
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ],
        CHANNEL_LAYERS={
            "default": {
                "BACKEND": "channels.layers.InMemoryChannelLayer",
            }
        },
        LOGGING_CONFIG=None,
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


def pytest_configure(config):
    if not settings.configured:
        settings.configure(**_make_test_settings())
        settings.ROOT_URLCONF = "baghchal.urls"
        django.setup()


def pytest_collection_modifyitems(items):
    for item in items:
        if getattr(item, "function", None):
            import inspect

            if inspect.iscoroutinefunction(item.function):
                item.add_marker(pytest.mark.asyncio)


@pytest.fixture(autouse=True, scope="module")
def apply_django_migrations():
    """Ensure test database tables exist for model-based tests."""
    from django.db import connection
    from django.db import transaction
    from django.core.management import call_command

    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = OFF;")

    with transaction.atomic(using=connection.alias):
        call_command("migrate", verbosity=0, database=connection.alias)
        call_command("migrate", verbosity=0, database=connection.alias)
        call_command("migrate", verbosity=0, database=connection.alias)

    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = ON;")
