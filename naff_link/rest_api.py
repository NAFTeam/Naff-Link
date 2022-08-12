async def resolve_track(self, track: str):
    headers = {"Authorization": self.ws.password}
    async with self.session.get(
        f"http://{self.ws.host}:{self.ws.port}/loadtracks?identifier={track}",
        headers=headers,
    ) as resp:
        data = await resp.json()
    return data["tracks"]
