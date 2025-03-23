from django.urls import path, include

app_name = 'game'

urlpatterns = [
    path('api/', include('game.api.urls')),
    path('', include('game.web.urls')),
]
