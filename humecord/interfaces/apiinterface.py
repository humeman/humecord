import humecord
from typing import Union

import time
import json
import asyncio
import httpx
import httpcore

from humecord.utils import (
    exceptions,
    debug
)

class APIInterface:
    def __init__(
            self
        ):
        
        self.endpoints = humecord.bot.config.globals.endpoints

        self.direct = DirectAPI(self)

        humecord.bot.api_online = True

    async def get(
            self,
            category: str,
            endpoint: str,
            args: dict,
            botapi_adapt: bool = True
        ):
        timer = time.time()

        # Find the category
        if category not in self.endpoints:
            raise humecord.utils.exceptions.InvalidRoute(f"Category {category} doesn't exist")

        current = self.endpoints[category]

        if endpoint not in current:
            raise humecord.utils.exceptions.InvalidRoute(f"Endpoint {endpoint} doesn't exist in category {category}")

        if "__override__" in current:
            base = getattr(humecord.bot.config, current["__override__"]["base"])
            auth = getattr(humecord.bot.config, current["__override__"]["auth"])

        else:
            base = humecord.bot.config.api_url
            auth = humecord.bot.config.auth

        route = current[endpoint]

        url = f"{base}/{route['endpoint']}".replace("%method%", "get")

        if route.get("auth"):
            args = {**args, **auth}

        try:
            data = await self.direct.get(url, args)

        except humecord.utils.exceptions.APIOffline:
            await self.handle_api_error()
            return

        if botapi_adapt:
            if not data.get("success"):
                # Check if bot ready error
                resend = await self.check_errors(data.get("error"), data.get("reason"))

                if resend:
                    return await self.get(category, endpoint, args, botapi_adapt)

            return data.get("data")

        else:
            return data

    async def put(
            self,
            category: str,
            endpoint: str,
            json_: dict,
            botapi_adapt: bool = True
        ):
        timer = time.time()

        # Find the category
        if category not in self.endpoints:
            raise humecord.utils.exceptions.InvalidRoute(f"Category {category} doesn't exist")

        current = self.endpoints[category]

        if endpoint not in current:
            raise humecord.utils.exceptions.InvalidRoute(f"Endpoint {endpoint} doesn't exist in category {category}")

        if "__override__" in current:
            base = getattr(humecord.bot.config, current["__override__"]["base"])
            auth = getattr(humecord.bot.config, current["__override__"]["auth"])

        else:
            base = humecord.bot.config.api_url
            auth = humecord.bot.config.auth

        route = current[endpoint]

        url = f"{base}/{route['endpoint']}".replace("%method%", "put")

        if route.get("auth"):
            json_ = {**json_, **auth}

        try:
            data = await self.direct.put(url, json_)

        except humecord.utils.exceptions.APIOffline:
            await self.handle_api_error()
            return

        if botapi_adapt:
            if not data.get("success"):
                # Check if bot ready error
                resend = await self.check_errors(data.get("error"), data.get("reason"))

                if resend:
                    return await self.put(category, endpoint, json_, botapi_adapt)

            if "data" in data:
                return data["data"]

        return data

    async def check_errors(
            self,
            etype: str,
            reason: str
        ):

        if type(reason) == str:
            # Check if "bot not ready" error
            if etype == "AuthError" and reason == f"Bot {humecord.bot.config.self_api} isn't ready":
                # Send ready info again
                await humecord.bot.syslogger.send(
                    "api",
                    embed = humecord.utils.discordutils.create_embed(
                        description = f"{humecord.bot.config.lang['emoji']['warning']}  **API has restarted - sending ready data again.**",
                        color = "warning"
                    )
                )

                await humecord.bot.events.call("on_ready", [None])

                # Resend request
                return True

        raise humecord.utils.exceptions.UnsuccessfulRequest(reason)

    async def handle_api_error(
            self
        ):   
        if humecord.bot.api_online:
            humecord.bot.api_online = False

            humecord.logger.log("api", "error", f"Bot API has gone offline. Pausing all requests.")

            try:
                await humecord.bot.syslogger.send(
                    "api",
                    embed = humecord.utils.discordutils.create_embed(
                        description = f"{humecord.bot.config.lang['emoji']['error']} **Lost connection to the bot API.**\n\nConnection failed for: `{humecord.bot.config.api_url}`\nPausing all events and loops until it returns.",
                        color = "error"
                    )
                )

            except:
                humecord.logger.log_step("api", "error", "Failed to log to debug channel.")
            
            # Reraise
            raise humecord.utils.exceptions.APIOffline("Failed to connect to bot API.")

        else:
            raise humecord.utils.exceptions.APIOffline("API is already offline. Something is still running! Report this to hume.")

class DirectAPI:
    def __init__(
            self,
            parent: APIInterface
        ):
        self.parent = parent

        limits = httpx.Limits(max_connections = 10)

        self.transport = httpx.AsyncHTTPTransport(limits = limits, retries = 2)
        self.client = httpx.AsyncClient(http2 = True)
        self.lock = False
        self.clients = []

    async def get(
            self,
            url: str, 
            args: Union[dict, None]
        ):
        if args is not None:
            if len(args) > 0:
                url += f"?{'&'.join([f'{key}={value}' for key, value in args.items()])}"

        response = await self._do(self.client.get(url))

        return response

    async def put(
            self,
            url: str, 
            json_: Union[dict, None]
        ):

        if json_ is None:
            kw = {}

        else:
            kw = {
                "data": json.dumps(json_)
            }

        response = await self._do(self.client.put(url, headers = {"content-type": "application/json"}, **kw))

        return response

    async def _do(
            self,
            coro
        ):
        try:
            response = await coro

            response.raise_for_status()

        except (httpcore.WriteError, httpcore.RemoteProtocolError, httpx.RemoteProtocolError) as e:
            raise

        except httpx.HTTPStatusError as e:
            raise humecord.utils.exceptions.APIError(f"API returned non-200 status code: {e.response.status_code}")

        except httpx.ConnectError as e:
            raise humecord.utils.exceptions.APIOffline()

        except httpx.RequestError as e:
            raise humecord.utils.exceptions.RequestError(f"Failed to send request to API")

        try:
            return response.json()

        except:
            raise exceptions.EmptyResponse(f"Response is missing JSON data")