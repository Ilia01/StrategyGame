from django.contrib import admin
from game.core.models import Game, Player, Unit, Building, Turn

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Admin interface for Game model"""
    list_display = ("name", "created_at", "current_turn", "is_active", "created_by")
    list_filter = ("is_active",)
    search_fields = ("name", "created_by__username")
    readonly_fields = ("created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    """Admin interface for Player model"""
    list_display = ("user", "game", "player_number", "is_active")
    list_filter = ("is_active", "game")
    search_fields = ("user__username", "game__name")
    raw_id_fields = ("user", "game")

class UnitInline(admin.TabularInline):
    """Inline admin for Units within Player"""
    model = Unit
    extra = 0
    fields = ("unit_type", "x_position", "y_position", "health")
    readonly_fields = ("created_at",)

class BuildingInline(admin.TabularInline):
    """Inline admin for Buildings within Player"""
    model = Building
    extra = 0
    fields = ("building_type", "x_position", "y_position", "health")
    readonly_fields = ("created_at",)

@admin.register(Turn)
class TurnAdmin(admin.ModelAdmin):
    """Admin interface for Turn model"""
    list_display = ("game", "player", "turn_number", "completed", "created_at")
    list_filter = ("completed", "game")
    search_fields = ("player__user__username", "game__name")
    readonly_fields = ("created_at", "completed_at")
