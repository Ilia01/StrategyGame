from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Game


class GameCreationForm(forms.ModelForm):
    """Form for creating a new game"""

    class Meta:
        model = Game
        fields = ["name", "map_size", "max_players"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter game name"}
            ),
            "map_size": forms.Select(attrs={"class": "form-select"}),
            "max_players": forms.Select(attrs={"class": "form-select"}),
        }
