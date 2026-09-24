"""Compose entry point with an explicit database on the persistent volume."""

from topolab.api import create_app

app = create_app(database_path="/data/topolab.sqlite3")
