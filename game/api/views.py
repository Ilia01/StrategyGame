from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from django.db import transaction
import logging

from game.core.models import Game, Player, Unit, Building
from game.services.game_service import GameService
from game.services.player_service import PlayerService
from game.mixins import GameServiceMixin
from .serializers import GameCreateSerializer, GameSerializer, PlayerSerializer
from .serializers import (
    BuildActionSerializer,
    MoveActionSerializer,
    AttackActionSerializer,
    TrainActionSerializer
)
from game.core.constants import (
    UNIT_TYPES,
    BUILDING_TYPES,
    TERRAIN_TYPES,
    MAP_SIZE_CHOICES,
    MAX_PLAYERS_CHOICES,
)
from game.core.game_rules import GAME_RULES 

logger = logging.getLogger(__name__)

class GameViewSet(viewsets.ModelViewSet, GameServiceMixin):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_service = GameService()
        self.player_service = PlayerService()
        self.game_service.player_service = self.player_service

    def get_queryset(self):
        return Game.objects.select_related(
            'created_by'
        ).prefetch_related(
            Prefetch('players', queryset=Player.objects.select_related('user')),
            'players__units',
            'players__buildings'
        ).all()

    @action(detail=False, methods=['post'])
    def create_game(self, request):
        serializer = GameCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            game = self.game_service.create_game(
                user=request.user,
                name=serializer.validated_data['name'],
                map_size=serializer.validated_data['map_size'],
                max_players=serializer.validated_data['max_players'],
            ) 
            logger.info(f"Game {game.name} created successfully by {request.user.username}"
            )
            return Response({
                "message": "Game created successfully"
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating game: {str(e)}", exc_info=True)
            return Response({"error": "Error creating game"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a game"""
        game = self.get_object()
        try:
            player = self.game_service.add_player(game, request.user)
            return Response(PlayerSerializer(player).data)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a game"""
        game = self.get_object()
        player = get_object_or_404(Player, user=request.user, game=game)
        self.player_service.deactivate_player(player)
        return Response({'status': 'success'})

    @action(detail=True, methods=['post'])
    def next_turn(self, request, pk=None):
        """Advance to next turn"""
        game = self.get_object()
        try:
            self.game_service.next_turn(game)
            return Response({'status': 'success'})
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def move_unit(self, request, pk=None):
        """Move a unit to new coordinates"""
        game = self.get_object()
        player = get_object_or_404(Player, user=request.user, game=game)
        
        unit_id = request.data.get('unit_id')
        x = request.data.get('x')
        y = request.data.get('y')
        
        try:
            self.game_service.move_unit(game, player, unit_id, x, y)
            return Response({'status': 'success'})
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def build_structure(self, request, pk=None):
        """Build a structure at specified coordinates"""
        game = self.get_object()
        player = get_object_or_404(Player, user=request.user, game=game)
        
        building_type = request.data.get('building_type')
        x = request.data.get('x')
        y = request.data.get('y')
        
        try:
            building = self.game_service.build_structure(game, player, building_type, x, y)
            return Response({'status': 'success', 'building_id': building.id})
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def train_unit(self, request, pk=None):
        game = self.get_object()
        player = get_object_or_404(Player, user=request.user, game=game)
        building_id = request.data.get('building_id')
        unit_type = request.data.get('unit_type')

        building = get_object_or_404(Building, id=building_id, player=player)
        
        try:
            unit = self.game_service.train_unit(building, unit_type)
            return Response({
                "message": "Unit trained successfully",
                "unit_id": unit.id
            })
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def take_turn(self, request, pk=None):
        game = self.get_object()
        player = get_object_or_404(Player, user=request.user, game=game)

        # Validate actions
        actions = request.data.get("actions", [])
        for action in actions:
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
                return Response(
                    {"error": f"Invalid action type: {action_type}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = self.game_service.process_turn_actions(game, player, actions)
            return Response({
                "message": "Turn completed successfully",
                "result": result
            })
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Server error during turn processing: {str(e)}", exc_info=True)
            return Response(
                {"error": "Server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def state(self, request, pk=None):
        """Get current game state"""
        game = self.get_object()
        current_player = self.game_service.get_current_player(game)
        active_players = self.game_service.get_active_players(game)
        
        return Response({
            'game_id': game.id,
            'current_turn': game.current_turn,
            'current_player': PlayerSerializer(current_player).data if current_player else None,
            'players': PlayerSerializer(active_players, many=True).data,
            'map_data': game.map_data
        })

    @action(detail=True, methods=['get'])
    def combat_stats(self, request, pk=None):
        game = self.get_object()
        player = get_object_or_404(Player, user=request.user, game=game)
        
        units = Unit.objects.filter(player=player)
        combat_stats = {
            unit.id: {
                'combat_power': self.game_service.calculate_combat_power(unit),
                'attack_range': self.game_service.is_in_attack_range(unit, None)
            }
            for unit in units
        }
        
        return Response(combat_stats)
    
    @action(detail=False, methods=['get'])
    def constants(self, request):
        return Response({
            'unit_types': UNIT_TYPES,
            'building_types': BUILDING_TYPES,
            'terrain_types': TERRAIN_TYPES,
            'map_size_choices': MAP_SIZE_CHOICES,
            'max_players_choices': MAX_PLAYERS_CHOICES,
            'game_rules': GAME_RULES
        })
