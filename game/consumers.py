import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from game.core.models import Game, Player, Unit, Building, Turn
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from game.services import GameService, GameStateService, ActionService, PlayerService


class GameConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_service = GameService()
        self.state_service = GameStateService()
        self.action_service = ActionService()
        self.player_service = PlayerService()

    async def connect(self):
        self.user = self.scope["user"]
        self.game_id = self.scope["url_route"]["kwargs"]["game_id"]
        self.room_group_name = f"game_{self.game_id}"

        # Verify user is part of the game
        if not await self.is_player_in_game():
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Remove from game group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        
        # Notify other players about disconnection
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_update",
                "update_type": "player_disconnected",
                "data": {
                    "player_id": self.user.id,
                    "username": self.user.username,
                }
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type")

        if message_type == "request_game_state":
            game_state = await self.get_game_state()
            await self.send(
                text_data=json.dumps({"type": "game_state", "state": game_state})
            )
        elif message_type == "chat_message":
            username = data.get("username", "Anonymous")
            message = data.get("message", "")

            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "chat_message", "username": username, "message": message},
            )
        elif message_type == "game_action":
            action_type = data.get("action_type")
            action_data = data.get("action_data", {})
            
            try:
                result = await self.handle_game_action(action_type, action_data)
                if result.get("success"):
                    # Broadcast game update to all players
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "game_update",
                            "update_type": action_type,
                            "data": result.get("data", {}),
                        }
                    )
                else:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": result.get("error", "Unknown error occurred")
                    }))
            except Exception as e:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": str(e)
                }))

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "username": event["username"],
                    "message": event["message"],
                }
            )
        )

    async def game_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "game_update",
            "update_type": event["update_type"],
            "data": event["data"]
        }))

    @database_sync_to_async
    def is_player_in_game(self):
        return self.player_service.is_player_in_game(self.user, self.game_id)

    @database_sync_to_async
    def get_game_state(self):
        return self.state_service.get_game_state(self.game_id, self.user)

    @database_sync_to_async
    def handle_game_action(self, action_type, action_data):
        try:
            return self.action_service.process_action(
                game_id=self.game_id,
                user=self.user,
                action_type=action_type,
                action_data=action_data
            )
        except Exception as e:
            return {"success": False, "error": str(e)}
