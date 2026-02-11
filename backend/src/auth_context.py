from contextvars import ContextVar

# Context dictionary to store user information for the current request
# We use a ContextVar to ensure thread-safety with async requests
is_mock_user_context: ContextVar[bool] = ContextVar("is_mock_user_context", default=False)

def is_current_user_mock() -> bool:
    """
    Check if the user associated with the current request context is a mock user.
    """
    return is_mock_user_context.get()
