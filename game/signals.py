from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Game, Unit, Building, Turn


@receiver(post_save, sender=Turn)
def turn_completed(sender, instance, created, **kwargs):
    """Signal to notify when a turn is completed"""
    if instance.completed:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"game_{instance.game.id}",
            {
                "type": "game_update",
                "update_type": "turn_completed",
                "data": {
                    "turn_number": instance.turn_number,
                    "player_id": instance.player.id,
                },
            },
        )


@receiver([post_save, post_delete], sender=Unit)
@receiver([post_save, post_delete], sender=Building)
def entity_changed(sender, instance, **kwargs):
    """Signal to notify when units or buildings are changed"""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"game_{instance.player.game.id}",
        {
            "type": "game_update",
            "update_type": "entity_changed",
            "data": {
                "entity_type": "unit" if isinstance(instance, Unit) else "building",
                "action": "deleted" if kwargs.get("deleted", False) else "updated",
            },
        },
    )


@receiver(post_save, sender=Game)
def game_updated(sender, instance, **kwargs):
    """Signal to notify when game state changes"""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"game_{instance.id}",
        {
            "type": "game_update",
            "update_type": "game_state_changed",
            "data": {
                "current_turn": instance.current_turn,
                "is_active": instance.is_active,
            },
        },
    )
