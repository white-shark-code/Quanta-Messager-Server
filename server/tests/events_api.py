from typing import Any
from uuid import UUID

from httpx import Response

from .services import BasicAPI, client


class EventsAPI(BasicAPI):
    @staticmethod
    def get_events_private_chats(
        auth: dict[str, str],
    ) -> dict[str, Any]:
        response: Response = client.get(
            headers=auth,
            url='/events/dialogs/'
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    def mark_readed_private_chat(
        auth: dict[str, str],
        event_id: UUID
    ) -> None:
        response: Response = client.post(
            headers=auth,
            url=f'/event/dialog/readed/{event_id}'
        )

        assert response.status_code == 200
