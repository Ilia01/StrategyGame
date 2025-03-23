import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Game, Player, Unit, Building, Turn
from django.contrib.auth.models import User


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.game_id = self.scope["url_route"]["kwargs"]["game_id"]
        self.room_group_name = f"game_{self.game_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

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
        await self.send(
            text_data=json.dumps(
                {
                    "type": "game_update",
                    "update_type": event["update_type"],
                    "data": event["data"],
                }
            )
        )

    @database_sync_to_async
    def get_game_state(self):
        """Get the current state of the game"""
        try:
            game = Game.objects.get(id=self.game_id)

            players = []
            for player in Player.objects.filter(game=game):
                players.append(
                    {
                        "id": player.id,
                        "username": player.user.username,
                        "player_number": player.player_number,
                        "resources": player.resources,
                        "is_active": player.is_active,
                    }
                )

            units = []
            for unit in Unit.objects.filter(player__game=game):
                units.append(
                    {
                        "id": unit.id,
                        "player_id": unit.player.id,
                        "unit_type": unit.unit_type,
                        "x": unit.x_position,
                        "y": unit.y_position,
                        "health": unit.health,
                        "attack": unit.attack,
                        "defense": unit.defense,
                        "movement_range": unit.movement_range,
                        "attack_range": unit.attack_range,
                    }
                )

            buildings = []
            for building in Building.objects.filter(player__game=game):
                buildings.append(
                    {
                        "id": building.id,
                        "player_id": building.player.id,
                        "building_type": building.building_type,
                        "x": building.x_position,
                        "y": building.y_position,
                        "health": building.health,
                    }
                )

            current_player_number = (game.current_turn - 1) % game.max_players + 1
            try:
                current_player = Player.objects.get(
                    game=game, player_number=current_player_number
                )
                current_player_id = current_player.id
                current_player_username = current_player.user.username
            except Player.DoesNotExist:
                current_player_id = None
                current_player_username = None

            return {
                "game_id": game.id,
                "name": game.name,
                "current_turn": game.current_turn,
                "current_player_id": current_player_id,
                "current_player_username": current_player_username,
                "map_size": game.map_size,
                "map_data": game.get_map(),
                "players": players,
                "units": units,
                "buildings": buildings,
                "is_active": game.is_active,
            }
        except Game.DoesNotExist:
            return {"error": "Game not found"}
