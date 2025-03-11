from django.db import models
from django.contrib.auth.models import User
import json

# Create your models here.


class Game(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    current_turn = models.IntegerField(default=1)
    max_players = models.IntegerField(default=2)
    map_size = models.IntegerField(default=10)
    map_data = models.TextField(default="{}")

    def __str__(self):
        return self.name

    def get_map(self):
        try:
            return json.loads(self.map_data)
        except:
            return {}

    def set_map(self, map_data):
        self.map_data = json.dumps(map_data)


class Player(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="players")
    resources = models.IntegerField(default=100)
    joined_at = models.DateTimeField(auto_now_add=True)
    player_number = models.IntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["user", "game"]

    def __str__(self):
        return f"{self.user.username} in {self.game.name}"


class Unit(models.Model):
    UNIT_TYPES = (
        ("infantry", "Infantry"),
        ("archer", "Archer"),
        ("cavalry", "Cavalry"),
        ("siege", "Siege Engine"),
    )

    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="units")
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPES)
    x_position = models.IntegerField()
    y_position = models.IntegerField()
    health = models.IntegerField(default=100)
    attack = models.IntegerField(default=10)
    defense = models.IntegerField(default=5)
    movement_range = models.IntegerField(default=2)
    attack_range = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.get_unit_type_display()} at ({self.x_position}, {self.y_position})"
        )


class Building(models.Model):
    BUILDING_TYPES = (
        ("base", "Base"),
        ("barracks", "Barracks"),
        ("farm", "Farm"),
        ("mine", "Mine"),
    )

    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="buildings"
    )
    building_type = models.CharField(max_length=20, choices=BUILDING_TYPES)
    x_position = models.IntegerField()
    y_position = models.IntegerField()
    health = models.IntegerField(default=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_building_type_display()} at ({self.x_position}, {self.y_position})"


class Turn(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="turns")
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    turn_number = models.IntegerField()
    actions = models.TextField(default="[]")
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["game", "player", "turn_number"]

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
