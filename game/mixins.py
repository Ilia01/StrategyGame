from game.services.game_service import GameService

class GameServiceMixin:
    _game_service = None
    _service_class = GameService

    @property
    def game_service(self):
        if self._game_service is None:
            self._game_service = self._service_class()
        return self._game_service

    @game_service.setter
    def game_service(self, service):
        self._game_service = service
