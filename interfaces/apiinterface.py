import humecord
from typing import Union

import httpx

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

        # Find the category
        if category not in self.endpoints:
            raise humecord.utils.exceptions.InvalidRoute(f"Category {category} doesn't exist")

        current = self.endpoints[category]

        if endpoint not in current:
            raise humecord.utils.exceptions.InvalidRoute(f"Endpoint {endpoint} doesn't exist in category {category}")

        route = current[endpoint]

        url = f"{humecord.bot.config.api_url}/{route['endpoint']}".replace("%method%", "get")

        if route.get("auth"):
            args = {**args, **humecord.bot.config.auth}

        try:
            data = await self.direct.get(url, args)

        except humecord.utils.exceptions.APIOffline:
            await self.handle_api_error()

        if botapi_adapt:
            if not data.get("success"):
                raise humecord.utils.exceptions.UnsuccessfulRequest(data.get("reason"))

            return data.get("data")

        else:
            return data

    async def put(
            self,
            category: str,
            endpoint: str,
            json: dict,
            botapi_adapt: bool = True
        ):

        # Find the category
        if category not in self.endpoints:
            raise humecord.utils.exceptions.InvalidRoute(f"Category {category} doesn't exist")

        current = self.endpoints[category]

        if endpoint not in current:
            raise humecord.utils.exceptions.InvalidRoute(f"Endpoint {endpoint} doesn't exist in category {category}")

        route = current[endpoint]

        url = f"{humecord.bot.config.api_url}/{route['endpoint']}".replace("%method%", "put")

        if route.get("auth"):
            json = {**json, **humecord.bot.config.auth}

        try:
            print(json)
            data = await self.direct.put(url, json)

        except humecord.utils.exceptions.APIOffline:
            await self.handle_api_error()

        if botapi_adapt:
            if not data.get("success"):
                raise humecord.utils.exceptions.UnsuccessfulRequest(data.get("reason"))

            if "data" in data:
                return data["data"]

        return data

    async def handle_api_error(
            self
        ):   
        if humecord.bot.api_online:
            humecord.bot.api_online = False

            humecord.utils.logger.log("error", f"Bot API has gone offline. Pausing all requests.")

            try:
                await humecord.bot.debug_channel.send(
                    embed = humecord.utils.discordutils.create_embed(
                        description = f"{humecord.bot.config.lang['emoji']['error']} **Lost connection to the bot API.**\n\nConnection failed for: `{humecord.bot.config.api_url}`\nPausing all events and loops until it returns.",
                        color = "error"
                    )
                )

            except:
                humecord.utils.logger.log_step("Failed to log to debug channel.", "red")
            
            # Reraise
            raise humecord.utils.exceptions.APIOffline("Failed to connect to bot API.")

class DirectAPI:
    def __init__(
            self,
            parent: APIInterface
        ):
        self.parent = parent

        self.client = httpx.AsyncClient()

    async def get(
            self,
            url: str, 
            args: Union[dict, None]
        ):
        if args:
            args = [f"{key}={value}" for key, value in args.items()]

            if len(args) > 0:
                url += f"?{'&'.join(args)}"

        async with self.client as c:
            try:
                response = await c.get(url)

                response.raise_for_status()

            except httpx.HTTPStatusError as e:
                raise humecord.utils.exceptions.APIError(f"API returned non-200 status code: {e.response.status_code}.")

            except httpx.ConnectError as e:
                raise humecord.utils.exceptions.APIOffline()

            except httpx.RequestError as e:
                raise humecord.utils.exceptions.RequestError(f"Failed to send request to API.")

        try:
            return response.json()

        except:
            raise humecord.utils.exeptions.EmptyResponse("Response is missing JSON data.")

    async def put(
            self,
            url: str, 
            json: Union[dict, None]
        ):

        async with self.client as c:
            try:
                response = await c.put(url, json = json)

                response.raise_for_status()

            except httpx.HTTPStatusError as e:
                raise humecord.utils.exceptions.APIError(f"API returned non-200 status code: {e.response.status_code}.")

            except httpx.ConnectError as e:
                raise humecord.utils.exceptions.APIOffline()

            except httpx.RequestError as e:
                raise humecord.utils.exceptions.RequestError(f"Failed to send request to API.")

        try:
            return response.json()

        except:
            raise humecord.utils.exeptions.EmptyResponse("Response is missing JSON data.")

        



        