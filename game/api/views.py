from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from django.shortcuts import get_object_or_404

from game.core.models import Game, Player
from game.services.game_service import GameService
from game.mixins import GameServiceMixin
from .serializers.game import GameCreateSerializer, GameSerializer
from .serializers.action import BuildActionSerializer, MoveActionSerializer, AttackActionSerializer
from game.core.constants import (
    UNIT_TYPES,
    BUILDING_TYPES,
    TERRAIN_TYPES,
    MAP_SIZE_CHOICES,
    MAX_PLAYERS_CHOICES
)

class GameViewSet(viewsets.ModelViewSet, GameServiceMixin):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @action(detail=False, methods=['post'])
    def create_game(self, request):
        serializer = GameCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            game = self.game_service.create_game(
                user=request.user,
                **serializer.validated_data
            )
            return Response({"game_id": game.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        game = self.get_object()
        try:
            player = self.game_service.add_player_to_game(request.user, game)
            return Response({"success": True}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def take_turn(self, request, pk=None):
        game = self.get_object()
        player = get_object_or_404(Player, user=request.user, game=game)

        try:
            self.game_service.process_turn_actions(game, player, request.data.get("actions", []))
            return Response({"success": True}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "Server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def state(self, request, pk=None):
        game = self.get_object()
        serializer = self.get_serializer(game)
        return Response(serializer.data)

@api_view(['GET'])
def get_game_constants(request):
    """Return all game constants for frontend use"""
    return Response({
        'units': UNIT_TYPES,
        'buildings': BUILDING_TYPES,
        'terrain': TERRAIN_TYPES,
        'mapSizes': dict(MAP_SIZE_CHOICES),
        'playerCounts': dict(MAX_PLAYERS_CHOICES)
    })
