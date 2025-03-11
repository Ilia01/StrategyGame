from django.contrib import admin
from .models import Game, Player, Unit, Building, Turn

# Register your models here.


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "current_turn", "is_active", "max_players")
    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("user", "game", "player_number", "resources", "is_active")
    list_filter = ("is_active", "game")
    search_fields = ("user__username",)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("id", "player", "unit_type", "x_position", "y_position", "health")
    list_filter = ("unit_type", "player__game")
    search_fields = ("player__user__username",)


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "player",
        "building_type",
        "x_position",
        "y_position",
        "health",
    )
    list_filter = ("building_type", "player__game")
    search_fields = ("player__user__username",)


@admin.register(Turn)
class TurnAdmin(admin.ModelAdmin):
    list_display = ("id", "game", "player", "turn_number", "completed", "created_at")
    list_filter = ("completed", "game")
    search_fields = ("player__user__username",)
