from django import forms
from .core.constants import MAP_SIZE_CHOICES, MAX_PLAYERS_CHOICES

class GameCreationForm(forms.Form):
    """Form for creating a new game"""
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter game name',
            'class': 'w-full p-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    map_size = forms.ChoiceField(
        choices=MAP_SIZE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full bg-white dark:bg-gray-700 border border-gray-300 text-gray-700 dark:text-white py-2 px-3 rounded leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    max_players = forms.ChoiceField(
        choices=MAX_PLAYERS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full bg-white dark:bg-gray-700 border border-gray-300 text-gray-700 dark:text-white py-2 px-3 rounded leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )