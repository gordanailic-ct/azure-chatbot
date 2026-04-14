# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import sys
from datetime import datetime
from http import HTTPStatus
import requests
import os

import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler

from aiohttp import web
from aiohttp.web import Request, Response, json_response

from config.config import DefaultConfig
from services.extract_pdf_text import sync_new_documents

CONFIG = DefaultConfig()
# 👇 LOGGING SETUP
logger = logging.getLogger(__name__)
logger.addHandler(
    AzureLogHandler(
        connection_string=CONFIG.APPINSIGHTS_CONNECTION_STRING
    )
)
logger.setLevel(logging.INFO)

logger.info("Bot started")

#biblioteke iz Microsoft Bot Framework SDK-a.
from botbuilder.core import (
    TurnContext,
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity, ActivityTypes
sys.path.insert(0, os.path.dirname(__file__))

from bots.echo_bot import EchoBot
from config.config import DefaultConfig

CONFIG = DefaultConfig()

# Create adapter.
# See https://aka.ms/about-bot-adapter to learn more about how bots work.
ADAPTER = CloudAdapter(ConfigurationBotFrameworkAuthentication(CONFIG))


# Catch-all for errors.
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    logger.error(f"[on_turn_error] {error}")

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
    await context.send_activity(
        "To continue to run this bot, please fix the bot source code."
    )
    # Send a trace activity if we're talking to the Bot Framework Emulator
    if context.activity.channel_id == "emulator":
        # Create a trace activity that contains the error object
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.utcnow(),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
        )
        # Send a trace activity, which will be displayed in Bot Framework Emulator
        await context.send_activity(trace_activity)


ADAPTER.on_turn_error = on_error

# Create the Bot
BOT = EchoBot()


# Listen for incoming requests on /api/messages
async def messages(req: Request) -> Response:
    body = await req.json()
    logger.info(f"Incoming request: {body}")

    return await ADAPTER.process(req, BOT)


APP = web.Application(middlewares=[aiohttp_error_middleware])
APP.router.add_post("/api/messages", messages)

#async def messages_get(req: Request) -> Response:
#    print("GET /api/messages pogodjen", flush=True)
#   return Response(text="api/messages radi (GET test)", status=200)

#APP.router.add_get("/api/messages", messages_get)

async def widget(req: Request) -> Response:
    return web.FileResponse('./static/widget.js')

APP.router.add_get("/widget.js", widget)

async def banner(req: Request) -> Response:
    return web.FileResponse('./banner.png')

APP.router.add_get("/banner.png", banner)

# async def root(req: Request) -> Response:
#     return Response(text="Bot is running!", status=200)

# APP.router.add_get("/", root)

async def get_token(req: Request) -> Response:
    secret = CONFIG.DIRECT_LINE_SECRET

    response = requests.post(
         "https://europe.directline.botframework.com/v3/directline/tokens/generate",
        headers={
            "Authorization": f"Bearer {secret}"
        }
    )

    return web.json_response(response.json())

APP.router.add_get("/api/token", get_token)

async def sync_docs(req: Request) -> Response:
    try:
        result = sync_new_documents()
        return web.json_response({
            "success": True,
            "message": "Sync uspešno završen.",
            "result": result
        })
    except Exception as e:
        logger.error(f"Sync error: {e}")
        return web.json_response({
            "success": False,
            "message": str(e)
        }, status=500)
    
APP.router.add_post("/api/sync-docs", sync_docs)

async def index(req: Request) -> Response:
    if os.path.exists('./static/chat.html'):
        return web.FileResponse('./static/chat.html')
    return Response(text="App is running!", status=200)

APP.router.add_get("/", index)
APP.router.add_static("/static/", path="./static", name="static")
app = APP


if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 3978))
        web.run_app(APP, host="0.0.0.0", port=port)
    except Exception as error:
        raise error
