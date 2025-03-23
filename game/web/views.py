from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.views.generic.detail import DetailView
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect

from game.core.models import Game, Player
from game.forms import GameCreationForm
from game.services.game_service import GameService

class HomeView(LoginRequiredMixin, FormView):
    template_name = 'home.html'
    form_class = GameCreationForm
    success_url = reverse_lazy('game:home')

    def form_valid(self, form):
        try:
            game = GameService.create_game(
                user=self.request.user,
                name=form.cleaned_data['name'],
                map_size=int(form.cleaned_data['map_size']),
                max_players=int(form.cleaned_data['max_players'])
            )
            return super().form_valid(form)
        except ValueError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_games"] = Game.objects.filter(is_active=True)
        return context

class GameDetailView(LoginRequiredMixin, DetailView):
    model = Game
    template_name = 'game_detail.html'
    context_object_name = "game"
    pk_url_kwarg = "game_id"

    def get(self, request, *args, **kwargs):
        game = self.get_object()
        if not game.is_active:
            return redirect('game:home')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game = self.get_object()
        
        try:
            player = Player.objects.get(user=self.request.user, game=game)
            context.update({
                "player": player,
                "is_player": True,
                "player_number": player.player_number,
                "player_resources": player.resources
            })
        except Player.DoesNotExist:
            context.update({
                "player": None,
                "is_player": False
            })

        context.update({
            "game_id": game.id,
            "current_turn": game.current_turn,
            "map_size": game.map_size,
            "player_count": game.players.count(),
            "max_players": game.max_players
        })
        
        return context

class LeaveGameView(LoginRequiredMixin, View):
    def post(self, request, game_id):
        try:
            player = Player.objects.get(user=request.user, game_id=game_id)
            player.is_active = False
            player.save()
            messages.success(request, "Successfully left the game.")
        except Player.DoesNotExist:
            messages.error(request, "You are not part of this game.")
        return redirect('game:home')
