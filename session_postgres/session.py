# Copyright 2016-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import json
import logging

from odoo.service import security
from odoo.tools._vendor.sessions import SessionStore
import datetime

from . import json_encoding

# this is equal to the duration of the session garbage collector in
# odoo.http.session_gc()
DEFAULT_SESSION_TIMEOUT = 60 * 60 * 24 * 7  # 7 days in seconds
DEFAULT_SESSION_TIMEOUT_ANONYMOUS = 60 * 60 * 3  # 3 hours in seconds

_logger = logging.getLogger(__name__)

class PostgresSessionStore(SessionStore):
    """SessionStore that saves session to postgres"""

    def __init__(
        self,
        c,
        session_class=None,
        expiration=None,
        anon_expiration=None,
    ):
        super().__init__(session_class=session_class)
        self.c = c
        self.expiration = expiration
        self.anon_expiration = anon_expiration
        if expiration is None:
            self.expiration = DEFAULT_SESSION_TIMEOUT
        else:
            self.expiration = expiration
        if anon_expiration is None:
            self.anon_expiration = DEFAULT_SESSION_TIMEOUT_ANONYMOUS
        else:
            self.anon_expiration = anon_expiration

        self._init_db()
        

    def _init_db(self):
        with self.c.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    key CHAR(40) PRIMARY KEY,
                    context JSONB NOT NULL,
                    db VARCHAR(64) NOT NULL,
                    debug VARCHAR(20) NOT NULL,
                    uid INT,
                    session_token CHAR(64),
                    expired_at TIMESTAMP NOT NULL
                );
                """
            )
            self.c.commit()

    def save(self, session):
        expired_at = datetime.datetime.now()
        if session.uid:
            expired_at = expired_at + datetime.timedelta(seconds=self.expiration)
        else:
            expired_at = expired_at + datetime.timedelta(seconds=self.anon_expiration)
        _logger.debug("Saving session %s" % session.sid)
        with self.c.cursor() as cur:
            cur.execute(
                """INSERT INTO sessions (key, context, db, debug, uid, session_token, expired_at) 
                VALUES (%(key)s, %(context)s, %(db)s, %(debug)s, %(uid)s, %(session_token)s, %(expired_at)s)
                ON CONFLICT (key) DO 
                UPDATE SET context = %(context)s, db = %(db)s, debug = %(debug)s, uid = %(uid)s, session_token = %(session_token)s, expired_at = %(expired_at)s
                """,
                {
                    "key": session.sid,
                    "context": json.dumps(dict(session.context)),
                    "db": session.db,
                    "debug": session.debug,
                    "uid": session.uid,
                    "session_token": session.session_token,
                    "expired_at": expired_at
                }
            )
            self.c.commit()

    def delete(self, session):
        _logger.debug("Deleting session %s" % session.sid)
        with self.c.cursor() as cur:
            cur.execute("DELETE FROM sessions WHERE key = %s", (session.sid,))
            self.c.commit()

    def get(self, sid):
        if not self.is_valid_key(sid):
            _logger.debug(
                "session with invalid sid '%s' has been asked, " "returning a new one",
                sid,
            )
            return self.new()

        _logger.debug("Getting session %s" % sid)
        saved = None
        with self.c.cursor() as cur:
            cur.execute(f"SELECT context, db, debug, uid, session_token FROM sessions WHERE key = %s", (sid,))
            saved = cur.fetchone()

        if not saved:
            _logger.debug(
                "session with non-existent key '%s' has been asked, "
                "returning a new one",
                sid,
            )
            return self.new()
        try:
            data = {
                "context": saved[0],
                "db": saved[1],
                "debug": saved[2],
                "uid": saved[3],
                "session_token": saved[4],
            }
        except ValueError:
            _logger.debug(
                "session with for key '%s' has been asked, ",
                "but it has no data, so it will be reset",
                data = {}
            )
        return self.session_class(data, sid, False)
    
    def list(self):
        _logger.debug("Listing sessions")
        with self.c.cursor() as cur:
            cur.execute("SELECT key FROM sessions")
            return cur.fetchall()

    def rotate(self, session, env):
        self.delete(session)
        session.sid = self.generate_key()
        if session.uid and env:
            session.session_token = security.compute_session_token(session, env)
        self.save(session)

    def vacuum(self, max_lifetime=0):
        _logger.debug("Vacuuming sessions")
        with self.c.cursor() as cur:
            cur.execute("DELETE FROM sessions WHERE expired_at < %s", (datetime.datetime.now(),))
            self.c.commit()