class RESTClient:
    def __init__(self, naff_link):
        self.naff_link = naff_link
        self.session = naff_link.session

    @property
    def base_url(self):
        return f"http://{self.naff_link.host}:{self.naff_link.port}"

    @property
    def headers(self):
        return {"Authorization": self.naff_link.password}

    async def resolve_track(self, track):
        async with self.naff_link.session.get(
            f"{self.base_url}/loadtracks?identifier={track}", headers=self.headers
        ) as resp:
            return await resp.json()

    async def decode_track(self, track):
        async with self.naff_link.session.get(
            f"{self.base_url}/decodetrack?track={track}", headers=self.headers
        ) as resp:
            return await resp.json()

    async def route_planner_status(self):
        ...

    async def route_planner_unmark_failed(self, address: str):
        ...

    async def route_planner_unmark_all_failed(self):
        ...
