from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from game.models import Game, Player

def home(request):
    """Main page view showing active games."""
    active_games = Game.objects.filter(is_active=True)
    return render(request, "home.html", {"active_games": active_games})

@login_required
def game_detail(request, game_id):
    """Display a specific game."""
    game = get_object_or_404(Game, pk=game_id)
    try:
        player = Player.objects.get(user=request.user, game=game)
        is_player = True
    except Player.DoesNotExist:
        player = None
        is_player = False

    context = {
        "game": game,
        "player": player,
        "is_player": is_player,
        "game_id": game_id,
    }
    return render(request, "game_detail.html", context)
