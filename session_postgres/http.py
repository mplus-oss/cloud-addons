# Copyright 2016-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
# Ported to PostgreSQL by syahrial@mplus.software

import logging
import os

from odoo import http
from odoo.tools import config
from odoo.tools.func import lazy_property

from .session import PostgresSessionStore
from .strtobool import strtobool

_logger = logging.getLogger(__name__)

import psycopg2

def is_true(strval):
    return bool(strtobool(strval or "0".lower()))

url = os.environ.get("ODOO_SESSION_POSTGRES_URL")
expiration = os.environ.get("ODOO_SESSION_POSTGRES_EXPIRATION")
anon_expiration = os.environ.get("ODOO_SESSION_POSTGRES_EXPIRATION_ANONYMOUS")


@lazy_property
def session_store(self):
    c = psycopg2.connect(url)

    return PostgresSessionStore(
        c=c,
        expiration=expiration,
        anon_expiration=anon_expiration,
        session_class=http.Session,
    )


def purge_fs_sessions(path):
    for fname in os.listdir(path):
        path = os.path.join(path, fname)
        try:
            os.unlink(path)
        except OSError:
            _logger.warning("OS Error during purge of redis sessions.")


if is_true(os.environ.get("ODOO_SESSION_POSTGRES")):
    _logger.info(
        "HTTP sessions stored in PostgreSQL at %s" % os.environ.get("ODOO_SESSION_POSTGRES_URL")
    )
    http.Application.session_store = session_store
    # clean the existing sessions on the file system
    purge_fs_sessions(config.session_dir)
