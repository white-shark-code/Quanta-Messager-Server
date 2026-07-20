from typing import Any
from uuid import UUID

from httpx import Response

from .services import BasicAPI, client


class EventsAPI(BasicAPI):
    @staticmethod
    async def get_events_private_chats(
        auth: dict[str, str],
    ) -> dict[str, Any]:
        response: Response = await client.get(headers=auth, url="/event/dialogs/")

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def mark_readed_private_chat(auth: dict[str, str], event_id: UUID) -> None:
        response: Response = await client.post(
            headers=auth, url=f"/event/dialog/readed/{event_id}"
        )

        assert response.status_code == 200
