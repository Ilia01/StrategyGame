from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
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

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.map_size < GAME_MIN_MAP_SIZE or self.map_size > GAME_MAX_MAP_SIZE:
            raise ValidationError(f"Map size must be between {GAME_MIN_MAP_SIZE} and {GAME_MAX_MAP_SIZE}")
        if self.max_players < GAME_MIN_PLAYERS or self.max_players > GAME_MAX_PLAYERS:
            raise ValidationError(f"Players must be between {GAME_MIN_PLAYERS} and {GAME_MAX_PLAYERS}")

    def __str__(self):
        return self.name

    def get_map(self):
        try:
            return json.loads(self.map_data)
        except:
            return dict

    def set_map(self, map_data):
        self.map_data = json.dumps(map_data)

    def get_visible_cells(self, player):
        """Get cells visible to a player (fog of war)"""
        from game.utils.game_helpers import calculate_visibility_map
        return calculate_visibility_map(self, player)

    def get_current_player(self):
        """Get the current player"""
        current_player_number = (self.current_turn - 1) % self.max_players + 1
        return self.players.filter(player_number=current_player_number).first()

    def get_next_player_number(self):
        """Get the next available player number"""
        used_numbers = set(self.players.values_list('player_number', flat=True))
        for num in range(1, self.max_players + 1):
            if num not in used_numbers:
                return num
        return None

    def is_full(self):
        """Check if game has maximum number of players"""
        return self.players.filter(is_active=True).count() >= self.max_players

    def get_active_player_count(self):
        """Get number of active players"""
        return self.players.filter(is_active=True).count()

    def can_join(self, user):
        """Check if user can join the game"""
        if not self.is_active:
            return False, "Game is not active"
        if self.is_full():
            return False, "Game is full"
        if self.players.filter(user=user).exists():
            return False, "Already in game"
        return True, ""

    def add_player(self, user):
        """Add a new player to the game"""
        can_join, message = self.can_join(user)
        if not can_join:
            raise ValueError(message)

        next_number = self.get_next_player_number()
        if next_number is None:
            raise ValueError("No available player numbers")

        return Player.objects.create(
            user=user,
            game=self,
            player_number=next_number
        )
    
    def deactivate(self):
        """Properly deactivate a game"""
        self.is_active = False
        self.save()


class Player(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="players")
    player_number = models.PositiveSmallIntegerField()
    resources = models.PositiveIntegerField(default=100)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [
            ["user", "game"],
            ["game", "player_number"]
        ]
        ordering = ['player_number']

    def save(self, *args, **kwargs):
        if not self.pk and not self.player_number:
            self.player_number = self.game.get_next_player_number()
            if self.player_number is None:
                raise ValueError("No available player numbers")
        super().save(*args, **kwargs)

    def deactivate(self):
        """Properly deactivate a player"""
        self.is_active = False
        self.save()

        if self.game.get_active_player_count() == 0:
            self.game.deactivate()

    def __str__(self):
        return f"{self.user.username} in {self.game.name}"


class Unit(models.Model):
    UNIT_CHOICES = [(data['name'], data['display']) for data in UNIT_TYPES.values()]
    
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="units")
    unit_type = models.CharField(max_length=20, choices=UNIT_CHOICES)
    x_position = models.PositiveIntegerField()
    y_position = models.PositiveIntegerField() 
    health = models.PositiveIntegerField(default=100)
    attack = models.PositiveIntegerField(default=10)
    defense = models.PositiveIntegerField(default=5)
    movement_range = models.PositiveIntegerField(default=2)
    attack_range = models.PositiveIntegerField(default=1)
    has_moved = models.BooleanField(default=False)
    has_attacked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return (
            f"{self.get_unit_type_display()} at ({self.x_position}, {self.y_position})"
        )

class Building(models.Model):
    BUILDING_CHOICES = [(data['name'], data['display']) for data in BUILDING_TYPES.values()]
    
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="buildings")
    building_type = models.CharField(max_length=20, choices=BUILDING_CHOICES)
    x_position = models.PositiveIntegerField()
    y_position = models.PositiveIntegerField()
    health = models.PositiveIntegerField(default=200)
    resource_production = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_building_type_display()} at ({self.x_position}, {self.y_position})"


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

    def get_actions(self):
        try:
            return json.loads(self.actions)
        except:
            return []

    def add_action(self, action):
        actions = self.get_actions()
        actions.append(action)
        self.actions = json.dumps(actions)
        self.save()
