from http.server import BaseHTTPRequestHandler
import json
from telegram_bot import webhook_handler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests from Telegram."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # Process the webhook
        result = webhook_handler(json.loads(post_data))
        
        # Send response
        self.send_response(result.get('statusCode', 200))
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode()) 