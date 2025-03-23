from rest_framework import serializers
from game.core.models import Game

class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ['id', 'name', 'current_turn', 'map_size', 'map_data']

class GameCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    map_size = serializers.IntegerField(min_value=10, max_value=30)
    max_players = serializers.IntegerField(min_value=2, max_value=4)