"""response.py - Describes Responses to user input."""

class Response:
    """Simple container class for parser response types."""
    # Response types
    POOL = 1
    TRADITIONAL = 2
    DATABASE = 3

    def __init__(self, response_type, embed=None, content=None):
        self.type = response_type
        self.embed = embed
        self.content = content
        self.add_reaction = False
