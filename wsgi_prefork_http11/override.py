import werkzeug
import logging
from odoo.service import server

_logger = logging.getLogger(__name__)

class BaseWSGIServerNoBindHTTP11(server.BaseWSGIServerNoBind):
    def __init__(self, app):
        handler = werkzeug.serving.WSGIRequestHandler
        handler.protocol_version = "HTTP/1.1"
        werkzeug.serving.BaseWSGIServer.__init__(self, "127.0.0.1", 0, app, handler)
        # Directly close the socket. It will be replaced by WorkerHTTP when processing requests
        if self.socket:
            self.socket.close()

_logger.info("Monkeypatching odoo.service.server.BaseWSGIServerNoBind with wsgi_prefork_http11.BaseWSGIServerNoBindHTTP11")
server.BaseWSGIServerNoBind = BaseWSGIServerNoBindHTTP11