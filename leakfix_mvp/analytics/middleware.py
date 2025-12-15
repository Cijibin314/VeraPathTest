from threading import local

_thread_locals = local()

def get_current_user():
    """
    Returns the current user from the thread-local storage.
    """
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware:
    """
    Middleware to store the current user in thread-local storage.
    This allows us to access the user in signal handlers.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = request.user
        response = self.get_response(request)
        return response
