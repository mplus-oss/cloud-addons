import psycopg2
import json
import logging
from odoo import http
from odoo.tools import config
from odoo.http import request, Response
from odoo.addons.web.controllers import main


_logger = logging.getLogger(__name__)


def make_response_with_status(data, headers=None, cookies=None, status=200):
    response = Response(data, status=status, headers=headers)
    if cookies:
        for k, v in cookies.items():
            response.set_cookie(k, v)
    return response


class HealthzHome(main.Home):
    @http.route('/healthz', type='http', auth="none", save_session=False, methods=['GET'])
    def mplus_web_health(self):
        headers = [('Content-Type', 'application/json'),
                   ('Cache-Control', 'no-store')]
        healthcheck_ip_whitelist = [ip.strip() for ip in config.get('healthcheck_ip_whitelist', '').split(',')]

        # Old odoo versions don't use X-Forwarded-For headers for client IPs, since Odoo will be always behind
        # a reverse proxy, check the IP from there instead and treat incoming connections without X-Forwarded-For
        # header as safe. Make sure you configured your ingress properly
        if 'X-Forwarded-For' in request.httprequest.headers:
            remote_addr = request.httprequest.headers.get('X-Forwarded-For').split(',')[0].strip()
            if remote_addr not in healthcheck_ip_whitelist:
                return make_response_with_status('', headers, status=403)

        healthcheck_db_name = config.get('healthcheck_db_name', 'postgres')
        healthcheck_db_connect_timeout = config.get('healthcheck_db_connect_timeout', 3)
        
        try:
            db_user = config.get('db_user')
            db_password = config.get('db_password')
            db_host = config.get('db_host')
            db_port = config.get('db_port')
            with psycopg2.connect(dbname=healthcheck_db_name,
                                  user=db_user,
                                  password=db_password,
                                  host=db_host,
                                  port=db_port,
                                  connect_timeout=healthcheck_db_connect_timeout) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
        except psycopg2.OperationalError as e:
            data = json.dumps({
                'status': 'fail',
                'reason': 'Database not ready',
            })
            return make_response_with_status(data, headers, status=500)
        data = json.dumps({
            'status': 'pass',
        })
        return request.make_response(data, headers)


_logger.info("Monkeypatching odoo.addons.web.controllers.main.Home with healthcheck.HealthzHome")
main.Home = HealthzHome