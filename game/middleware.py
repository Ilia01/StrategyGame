from django.shortcuts import render

class GameErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, ValueError):
            return render(request, 'error.html', {
                'title': 'Game Error',
                'message': str(exception)
            }, status=400)
        return None