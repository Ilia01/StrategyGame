from rest_framework import serializers
from game.core.models import Building

class BuildActionSerializer(serializers.Serializer):
    type = serializers.CharField()
    building_type = serializers.ChoiceField(choices=Building.BUILDING_CHOICES)
    x = serializers.IntegerField(min_value=0)
    y = serializers.IntegerField(min_value=0)

class MoveActionSerializer(serializers.Serializer):
    type = serializers.CharField()
    unit_id = serializers.IntegerField()
    x = serializers.IntegerField(min_value=0)
    y = serializers.IntegerField(min_value=0)

class AttackActionSerializer(serializers.Serializer):
    type = serializers.CharField()
    unit_id = serializers.IntegerField()
    target_x = serializers.IntegerField(min_value=0)
    target_y = serializers.IntegerField(min_value=0)