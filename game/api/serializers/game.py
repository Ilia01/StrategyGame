from rest_framework import serializers
from game.core.models import Game, Player, Unit, Building

class PlayerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    resources = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = ['id', 'username', 'player_number', 'resources']

    def get_resources(self, obj):
        return obj.resources

class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'unit_type', 'x_position', 'y_position', 'health', 
                 'attack', 'defense', 'movement_range', 'attack_range',
                 'has_moved', 'has_attacked']

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ['id', 'building_type', 'x_position', 'y_position', 'health',
                 'resource_production']

class GameSerializer(serializers.ModelSerializer):
    players = PlayerSerializer(many=True, read_only=True)
    units = UnitSerializer(many=True, read_only=True)
    buildings = BuildingSerializer(many=True, read_only=True)
    current_player = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = ['id', 'name', 'current_turn', 'map_size', 'map_data',
                 'current_player', 'players', 'units', 'buildings']

    def get_current_player(self, obj):
        if obj.current_player:
            return PlayerSerializer(obj.current_player).data
        return None

class GameCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    map_size = serializers.IntegerField(min_value=10, max_value=30)
    max_players = serializers.IntegerField(min_value=2, max_value=4)