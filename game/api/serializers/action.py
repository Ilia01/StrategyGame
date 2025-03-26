from rest_framework import serializers
from game.core.models import Building, Unit
from game.core.constants import UNIT_TYPES, BUILDING_TYPES

class BaseActionSerializer(serializers.Serializer):
    type = serializers.CharField()

class BuildActionSerializer(BaseActionSerializer):
    building_type = serializers.ChoiceField(choices=BUILDING_TYPES.keys())
    x = serializers.IntegerField(min_value=0)
    y = serializers.IntegerField(min_value=0)

    def validate(self, data):
        if data['building_type'] not in BUILDING_TYPES:
            raise serializers.ValidationError(f"Invalid building type: {data['building_type']}")
        return data

class MoveActionSerializer(BaseActionSerializer):
    unit_id = serializers.IntegerField()
    x = serializers.IntegerField(min_value=0)
    y = serializers.IntegerField(min_value=0)

    def validate_unit_id(self, value):
        try:
            Unit.objects.get(id=value)
        except Unit.DoesNotExist:
            raise serializers.ValidationError(f"Unit with id {value} does not exist")
        return value

class AttackActionSerializer(BaseActionSerializer):
    unit_id = serializers.IntegerField()
    target_x = serializers.IntegerField(min_value=0)
    target_y = serializers.IntegerField(min_value=0)

    def validate_unit_id(self, value):
        try:
            Unit.objects.get(id=value)
        except Unit.DoesNotExist:
            raise serializers.ValidationError(f"Unit with id {value} does not exist")
        return value

class TrainActionSerializer(BaseActionSerializer):
    barracks_id = serializers.IntegerField()
    unit_type = serializers.ChoiceField(choices=UNIT_TYPES.keys())

    def validate(self, data):
        if data['unit_type'] not in UNIT_TYPES:
            raise serializers.ValidationError(f"Invalid unit type: {data['unit_type']}")
        
        try:
            barracks = Building.objects.get(id=data['barracks_id'])
            if barracks.building_type != 'barracks':
                raise serializers.ValidationError("Building must be a barracks")
        except Building.DoesNotExist:
            raise serializers.ValidationError(f"Barracks with id {data['barracks_id']} does not exist")
        
        return data

class ActionListSerializer(serializers.Serializer):
    actions = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=True
    )

    def validate_actions(self, value):
        for action in value:
            action_type = action.get('type')
            if action_type == 'build':
                serializer = BuildActionSerializer(data=action)
            elif action_type == 'move_unit':
                serializer = MoveActionSerializer(data=action)
            elif action_type == 'attack':
                serializer = AttackActionSerializer(data=action)
            elif action_type == 'train_unit':
                serializer = TrainActionSerializer(data=action)
            else:
                raise serializers.ValidationError(f"Invalid action type: {action_type}")

            if not serializer.is_valid():
                raise serializers.ValidationError(serializer.errors)
        
        return value