from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.views.generic.detail import DetailView
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Prefetch

from game.core.models import Game, Player
from game.forms import GameCreationForm
from game.services.game_service import GameService
from game.api.serializers.game import GameSerializer
from game.mixins import GameServiceMixin
class HomeView(LoginRequiredMixin,GameServiceMixin, FormView):
    template_name = 'home.html'
    form_class = GameCreationForm

    def form_valid(self, form):
        try:
            game = self.game_service.create_game(
                user=self.request.user,
                name=form.cleaned_data['name'],
                map_size=int(form.cleaned_data['map_size']),
                max_players=int(form.cleaned_data['max_players'])
            )
            self.created_game_id = game.id
            messages.success(self.request, "Game created successfully!")
            return redirect('game:game_detail', game_id=game.id)
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)

    def get_success_url(self):
        return reversed('game:game_detail', kwargs={'game_id': self.created_game_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        active_games = Game.objects.filter(
            is_active=True
        ).select_related('created_by').prefetch_related('players')
        
        my_games = Game.objects.filter(
            players__user=self.request.user,
            is_active=True
        ).distinct()

        context.update({
            'active_games': active_games,
            'my_games': my_games,
            'serialized_games': GameSerializer(active_games, many=True).data
        })
        return context

class GameDetailView(LoginRequiredMixin, DetailView):
    model = Game
    template_name = 'game_detail.html'
    context_object_name = 'game'
    pk_url_kwarg = 'game_id'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Game.objects.select_related('created_by').prefetch_related(
                Prefetch('players', queryset=Player.objects.select_related('user'))
            ),
            id=self.kwargs['game_id']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game = self.object
        
        try:
            player = Player.objects.get(user=self.request.user, game=game)
            context.update({
                'player': player,
                'is_player': True,
                'player_number': player.player_number,
                'player_resources': player.resources,
                'is_current_player': game.get_current_player() == player
            })
        except Player.DoesNotExist:
            context.update({
                'player': None,
                'is_player': False,
                'can_join': game.players.count() < game.max_players
            })

        # Add game state data for frontend
        game_state = GameSerializer(game).data
        context.update({
            'game_state': game_state,
            'current_player': game.get_current_player(),
            'player_count': game.players.count(),
            'max_players': game.max_players
        })
        
        return context

class JoinGameView(LoginRequiredMixin, GameServiceMixin, View):
    def post(self, request, game_id):
        game = get_object_or_404(Game, id=game_id)
        
        try:
            self.game_service.add_player_to_game(request.user, game)
            messages.success(request, "Successfully joined the game!")
            return redirect('game:game_detail', game_id=game_id)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('game:home')

class LeaveGameView(LoginRequiredMixin, GameServiceMixin, View):
    def post(self, request, game_id):
        game = get_object_or_404(Game, id=game_id)
        
        try:
            self.game_service.remove_player_from_game(request.user, game)
            messages.success(request, "Successfully left the game.")
        except Exception as e:
            messages.error(request, str(e))
        
        return redirect('game:home')
