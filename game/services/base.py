from abc import ABC, abstractmethod

class BaseGameService(ABC):
    """Base class for all game-related services"""
    pass

class BaseStateService(BaseGameService):
    """Handles game state management"""
    @abstractmethod
    def get_game_state(self, game_id, user):
        pass

    @abstractmethod
    def get_home_page_state(self, user):
        pass

class BasePlayerService(BaseGameService):
    """Handles player management"""
    @abstractmethod
    def add_player(self, user, game):
        pass

    @abstractmethod
    def remove_player(self, user, game):
        pass

class BaseCombatService(BaseGameService):
    """Handles combat operations"""
    @abstractmethod
    def process_attack(self, unit, target):
        pass

class BaseActionService(BaseGameService):
    """Handles turn actions"""
    @abstractmethod
    def process_turn_actions(self, game, player, actions):
        pass