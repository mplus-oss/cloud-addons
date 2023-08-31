import psycopg2
import json
import logging
from odoo import http
from odoo.tools import config
from odoo.http import request
from odoo.addons.web.controllers import home


_logger = logging.getLogger(__name__)


class HealthzHome(home.Home):
    @http.route('/healthz', type='http', auth="none", save_session=False, methods=['GET'])
    def mplus_web_health(self):
        headers = [('Content-Type', 'application/json'),
                   ('Cache-Control', 'no-store')]
        healthcheck_ip_whitelist = [ip.strip() for ip in config.get('healthcheck_ip_whitelist', '').split(',')]
        if request.httprequest.remote_addr not in healthcheck_ip_whitelist:
            return request.make_response('', headers, status=403)
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
            return request.make_response(data, headers, status=500)
        data = json.dumps({
            'status': 'pass',
        })
        return request.make_response(data, headers)


_logger.info("Monkeypatching odoo.addons.web.controllers.home.Home with healthcheck.HealthzHome")
home.Home = HealthzHome