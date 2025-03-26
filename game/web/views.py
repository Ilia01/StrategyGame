from django.urls import reverse, reverse_lazy
from django.views.generic.edit import FormView
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from django.db.models import Prefetch
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.core.cache import cache
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from game.core.models import Game, Player, Unit
from game.core.game_rules import GAME_RULES
from game.forms import GameCreationForm
from game.services.game_service import GameService
from game.api.serializers.game import GameSerializer
from game.mixins import GameServiceMixin

class HomeView(LoginRequiredMixin, GameServiceMixin, FormView):
    template_name = 'home.html'
    form_class = GameCreationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.game_service.get_home_page_state(self.request.user))
        return context

    def form_valid(self, form):
        try:
            game = self.game_service.create_game(
                user=self.request.user,
                name=form.cleaned_data['name'],
                map_size=int(form.cleaned_data['map_size']),
                max_players=int(form.cleaned_data['max_players'])
            )
            messages.success(self.request, "Game created successfully!")
            return redirect('game:game_detail', game_id=game.id)
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

class GameDetailView(LoginRequiredMixin, GameServiceMixin, View):
    template_name = 'game_detail.html'

    def get(self, request, *args, **kwargs):
        game_id = kwargs['game_id']
        context = self.game_service.get_game_state(game_id, request.user)
        return render(request, self.template_name, context)

    @method_decorator(require_http_methods(["POST"]))
    def post(self, request, *args, **kwargs):
        game_id = kwargs['game_id']
        game = get_object_or_404(Game, id=game_id)
        player = get_object_or_404(Player, user=request.user, game=game)
        
        try:
            actions = request.POST.getlist('actions[]')
            result = self.game_service.process_turn_actions(game, player, actions)
            return JsonResponse({
                'success': True,
                'message': 'Turn completed successfully',
                'result': result
            })
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'Server error',
                'details': str(e)
            }, status=500)

class JoinGameView(LoginRequiredMixin, GameServiceMixin, View):
    def post(self, request, game_id):
        game = get_object_or_404(Game, id=game_id)
        
        try:
            player = self.game_service.manage_player_in_game(request.user, game, 'add')
            messages.success(request, f"Successfully joined the game as player {player.player_number}!")
            return redirect('game:game_detail', game_id=game_id)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('game:home')

class LeaveGameView(LoginRequiredMixin, GameServiceMixin, View):
    http_method_names = ['post']  # Only allow POST method
    
    def post(self, request, game_id):
        game = get_object_or_404(Game, id=game_id)
        
        try:
            self.game_service.manage_player_in_game(request.user, game, 'remove')
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"game_{game_id}",
                {
                    "type": "game_update",
                    "update_type": "player_left",
                    "data": {
                        "player_id": request.user.id,
                        "username": request.user.username,
                    }
                }
            )
            
            messages.success(request, "Successfully left the game.")
            return redirect('game:home')
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('game:home')

class GameCombatStatsView(LoginRequiredMixin, GameServiceMixin, View):
    def get(self, request, game_id):
        game = get_object_or_404(Game, id=game_id)
        player = get_object_or_404(Player, user=request.user, game=game)
        
        units = Unit.objects.filter(player=player)
        combat_stats = {
            unit.id: {
                'combat_power': self.game_service.calculate_combat_power(unit),
                'attack_range': self.game_service.is_in_attack_range(unit, None)
            }
            for unit in units
        }
        
        return JsonResponse(combat_stats)
