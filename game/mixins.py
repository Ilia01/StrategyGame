from game.services import GameService

class GameServiceMixin():
  game_service = GameService
  
  def get_game_service(self):
    return self.game_service
