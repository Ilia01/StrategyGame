from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from .constants import (
    GAME_MIN_MAP_SIZE, 
    GAME_MAX_MAP_SIZE,
    GAME_MIN_PLAYERS,
    GAME_MAX_PLAYERS,
    UNIT_TYPES,
    BUILDING_TYPES
)
import json

class Game(models.Model):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    current_turn = models.IntegerField(default=1)
    max_players = models.PositiveSmallIntegerField(default=2)
    map_size = models.PositiveIntegerField(default=10)
    map_data = models.JSONField(default=dict)
    current_player_index = models.PositiveSmallIntegerField(default=0)
    game_state = models.JSONField(default=dict)  # Stores game state like resources, etc.

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.map_size < GAME_MIN_MAP_SIZE or self.map_size > GAME_MAX_MAP_SIZE:
            raise ValidationError(f"Map size must be between {GAME_MIN_MAP_SIZE} and {GAME_MAX_MAP_SIZE}")
        if self.max_players < GAME_MIN_PLAYERS or self.max_players > GAME_MAX_PLAYERS:
            raise ValidationError(f"Players must be between {GAME_MIN_PLAYERS} and {GAME_MAX_PLAYERS}")

    def __str__(self):
        return self.name

    @property
    def current_player(self):
        """Get the current player"""
        if not self.players.exists():
            return None
        return self.players.all()[self.current_player_index]

    @property
    def active_players(self):
        """Get all active players"""
        return self.players.filter(is_active=True)

    @property
    def is_full(self):
        """Check if game has maximum number of players"""
        return self.active_players.count() >= self.max_players

    def can_join(self, user):
        """Check if user can join the game"""
        if not self.is_active:
            return False, "Game is not active"
        if self.is_full:
            return False, "Game is full"
        if self.players.filter(user=user).exists():
            return False, "Already in game"
        return True, ""

    def add_player(self, user):
        """Add a new player to the game"""
        can_join, message = self.can_join(user)
        if not can_join:
            raise ValueError(message)

        player = Player.objects.create(
            user=user,
            game=self,
            player_number=self.active_players.count() + 1
        )
        
        # Initialize player state
        self.game_state[str(player.id)] = {
            'resources': 100,
            'units': [],
            'buildings': []
        }
        self.save()
        return player

    def next_turn(self):
        """Advance to the next turn"""
        self.current_turn += 1
        self.current_player_index = (self.current_player_index + 1) % self.active_players.count()
        self.save()

    def deactivate(self):
        """Properly deactivate a game"""
        self.is_active = False
        self.save()

class Player(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="players")
    player_number = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [
            ["user", "game"],
            ["game", "player_number"]
        ]
        ordering = ['player_number']

    def __str__(self):
        return f"{self.user.username} in {self.game.name}"

    @property
    def resources(self):
        """Get player's resources from game state"""
        return self.game.game_state.get(str(self.id), {}).get('resources', 0)

    def deactivate(self):
        """Properly deactivate a player"""
        self.is_active = False
        self.save()

        if self.game.active_players.count() == 0:
            self.game.deactivate()

class GameEntity(models.Model):
    """Base class for game entities (units and buildings)"""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="%(class)ss")
    x_position = models.PositiveIntegerField()
    y_position = models.PositiveIntegerField()
    health = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.__class__.__name__} at ({self.x_position}, {self.y_position})"

class Unit(GameEntity):
    UNIT_CHOICES = [(data['name'], data['display']) for data in UNIT_TYPES.values()]
    
    unit_type = models.CharField(max_length=20, choices=UNIT_CHOICES)
    attack = models.PositiveIntegerField(default=10)
    defense = models.PositiveIntegerField(default=5)
    movement_range = models.PositiveIntegerField(default=2)
    attack_range = models.PositiveIntegerField(default=1)
    has_moved = models.BooleanField(default=False)
    has_attacked = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

class Building(GameEntity):
    BUILDING_CHOICES = [(data['name'], data['display']) for data in BUILDING_TYPES.values()]
    
    building_type = models.CharField(max_length=20, choices=BUILDING_CHOICES)
    resource_production = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['created_at']

class Turn(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="turns")
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    turn_number = models.PositiveIntegerField()
    actions = models.JSONField(default=list)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["game", "player", "turn_number"]
        ordering = ['turn_number', 'created_at']

    def clean(self):
        if self.turn_number < 1:
            raise ValidationError("Turn number must be positive")

    def __str__(self):
        return f"Turn {self.turn_number} by {self.player.user.username} in {self.game.name}"

    def complete(self):
        """Mark turn as completed"""
        self.completed = True
        self.completed_at = timezone.now()
        self.save()
