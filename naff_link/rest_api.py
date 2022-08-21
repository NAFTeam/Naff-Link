class RESTClient:
    def __init__(self, naff_link, instance):
        self.naff_link = naff_link
        self.instance = instance
        self.session = naff_link.session

    @property
    def base_url(self):
        return f"http://{self.instance.host}:{self.instance.port}"

    @property
    def headers(self):
        return {"Authorization": self.instance.password}

    async def request(self, method, url, **kwargs) -> dict:
        """
        Makes a request to the REST API.

        Args:
            method: The HTTP method to use.
            url: The URL to request.
            **kwargs: Any additional arguments to pass to aiohttp.request.

        Returns:
            The json response.
        """
        async with self.session.request(method, url, headers=self.headers, **kwargs) as resp:
            return await resp.json()

    async def resolve_track(self, track):
        return await self.request("GET", f"{self.base_url}/loadtracks?identifier={track}")

    async def decode_track(self, track):
        return await self.request("GET", f"{self.base_url}/decodetrack?track={track}")

    async def route_planner_status(self):
        ...

    async def route_planner_unmark_failed(self, address: str):
        ...

    async def route_planner_unmark_all_failed(self):
        ...
