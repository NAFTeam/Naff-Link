from attr import field
from lavalink import Event
from naff.api.events import BaseEvent
from naff.client.utils import define, docs


@define(kw_only=False)
class NaffLinkEvent(BaseEvent):
    link_event: Event = field(metadata=docs("The Lavalink link_event"))
    """The Lavalink link_event"""
