# Sessions in PostgreSQL

This addon allows to store the web sessions in a PostgreSQL Database.

## Configuration

The storage of sessions in PostgreSQL is activated using environment variables.

* `ODOO_SESSION_POSTGRES` has to be `1` or `true`
* `ODOO_SESSION_POSTGRES_URL` is the connection string (e.g. `postgres://odoo_sessions:p4ssw0rd@postgresql.postgresql.svc:5432/odoo_sessions`)
* `ODOO_SESSION_POSTGRES_EXPIRATION` is the time in seconds before expiration of the sessions (default is 7 days)
* `ODOO_SESSION_POSTGRES_EXPIRATION_ANONYMOUS` is the time in seconds before expiration of the anonymous sessions (default is 3 hours)

This addon must be added in the server wide addons with (`--load` option):

```--load=web,session_postgres```

## Limitations

* The server has to be restarted in order for the sessions to be stored in
  PostgreSQL.
* All the users will have to login again as their previous session will be
  dropped.
* The addon monkey-patch `odoo.http.Root.session_store` with a custom
  method when the PostgreSQL mode is active, so incompatibilities with other addons
  is possible if they do the same.

# Original Authors
[Camptocamp SA (2016-2019)](https://github.com/camptocamp/odoo-cloud-platform/tree/16.0/session_redis)