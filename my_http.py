import os
import json
from http.server import BaseHTTPRequestHandler

class WebServer(BaseHTTPRequestHandler):
    def __init__(self, collars, *args, **kwargs):
        self.collars = collars
        super().__init__(*args, **kwargs)

    def json(self, data):
        json_text = json.dumps(data, indent=2)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json_text.encode('utf-8'))

    def html(self, html):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def do_GET(self):
        if self.path == '/api/state':
            self.json({ "collars": self.collars.status(), "path": self.path })
        else:
            self.html('<html><head><title>SARTopo In A Box</title></head><body>Hi there!</body></html>')
