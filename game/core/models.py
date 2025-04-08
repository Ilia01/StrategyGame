from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from .constants import UNIT_TYPES, BUILDING_TYPES
from django.utils import timezone

class Game(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="created_games", null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    max_players = models.IntegerField(default=2)
    map_size = models.CharField(
        max_length=20,
        validators=[MinValueValidator(10), MaxValueValidator(20)],
        default=10,
    )
    map_data = models.JSONField(default=dict, blank=True)
    current_turn = models.IntegerField(default=1)
    current_player_index = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} (Turn {self.current_turn})"

class Player(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="players")
    player_number = models.IntegerField()
    is_active = models.BooleanField(default=True)
    resources = models.IntegerField(default=100, null=True, blank=True)
    
    class Meta:
        unique_together = ['game', 'player_number']
        ordering = ['player_number']
        
    def __str__(self):
        return f"{self.user.username} (Player {self.player_number})"

class GameEntity(models.Model):
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
    turn_number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['game', 'player', 'turn_number']
        ordering = ['turn_number', 'player']
        
    def __str__(self):
        return f"Turn {self.turn_number} - {self.player.user.username}"
