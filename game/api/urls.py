from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'games', views.GameViewSet)

urlpatterns = router.urls + [
    path('constants/', views.get_game_constants, name='game-constants'),
]