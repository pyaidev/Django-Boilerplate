"""Collect immutable static assets during the image build, without runtime secrets."""

from .base import *  # noqa: F403

SECRET_KEY = "build-only-secret-key-0123456789-abcdefghijklmnopqrstuvwxyz"
