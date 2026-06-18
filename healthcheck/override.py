import psycopg2
import json
import logging
from odoo import http
from odoo.tools import config
from odoo.http import request


_logger = logging.getLogger(__name__)


class HealthzController(http.Controller):
    @http.route('/healthz', type='http', auth="none", save_session=False, methods=['GET'])
    def mplus_web_health(self):
        ip_whitelist_str = config.get('healthcheck_ip_whitelist', '')
        headers = [('Content-Type', 'application/json'),
                   ('Cache-Control', 'no-store')]
        healthcheck_ip_whitelist = [ip.strip() for ip in str(ip_whitelist_str).split(',')]

        if not {'0.0.0.0', '127.0.0.1'} <= set(healthcheck_ip_whitelist):
            # Since Odoo will be always behind a reverse proxy, X-Forwarded-For being exist indicates that the request comes from
            # public network, treat incoming connections without X-Forwarded-For header as safe. Make sure you configured your ingress
            # properly.
            if 'X-Forwarded-For' in request.httprequest.headers:
                client_ip = request.httprequest.headers.get('X-Forwarded-For').split(',')[0].strip()
                if client_ip not in healthcheck_ip_whitelist:
                    return request.make_response(
                        json.dumps({ 'status': 'denied' }),
                        headers, status=403)

        healthcheck_db_name = config.get('healthcheck_db_name', 'postgres')
        healthcheck_db_connect_timeout = config.get('healthcheck_db_connect_timeout', 3)

        try:
            db_user = config.get('db_user')
            db_password = config.get('db_password')
            db_host = config.get('db_host')
            db_port = config.get('db_port')
            connect_timeout = int(str(healthcheck_db_connect_timeout))
            with psycopg2.connect(dbname=healthcheck_db_name,
                                  user=db_user,
                                  password=db_password,
                                  host=db_host,
                                  port=db_port,
                                  connect_timeout=connect_timeout) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
        except psycopg2.OperationalError as _:
            return request.make_response(
                json.dumps({ 'status': 'fail', 'reason': 'Database not ready' }),
                headers, status=500)

        return request.make_response(
            json.dumps({ 'status': 'pass', 'reason': 'OK' }),
            headers)


_logger.info("Server-wide controller ‘healthcheck’ has been successfully loaded. The /healthz endpoint is now active.")
if not config.get('healthcheck_ip_whitelist'):
    _logger.warning(
        "healthcheck_ip_whitelist is not configured. The /healthz endpoint is open to all IPs."
    )
