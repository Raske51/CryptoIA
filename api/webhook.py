from http.server import BaseHTTPRequestHandler
import json
import os
from telegram import Update
from telegram.ext import Application, CommandHandler
from telegram_bot import start, help_command, status, settings, trade
import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def process_update(update_data):
    """Process Telegram update data."""
    try:
        TOKEN = os.getenv('TELEGRAM_TOKEN')
        if not TOKEN:
            raise ValueError("TELEGRAM_TOKEN not found in environment variables")

        app = Application.builder().token(TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("status", status))
        app.add_handler(CommandHandler("settings", settings))
        app.add_handler(CommandHandler("trade", trade))

        # Process update
        update = Update.de_json(update_data, app.bot)
        await app.process_update(update)
        
        return {"statusCode": 200, "body": "success"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"statusCode": 500, "body": str(e)}

def handler(event, context):
    """Serverless function handler for Vercel."""
    try:
        # Parse the incoming request body
        if isinstance(event.get('body'), str):
            update_data = json.loads(event['body'])
        else:
            update_data = event.get('body', {})

        # Process the update
        import asyncio
        result = asyncio.run(process_update(update_data))
        
        return {
            'statusCode': result.get('statusCode', 200),
            'body': json.dumps(result)
        }
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(e)})
        }

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