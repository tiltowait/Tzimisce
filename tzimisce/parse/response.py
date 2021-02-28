"""response.py - Describes Responses to user input."""

class Response:
    # Response types
    POOL = 1
    TRADITIONAL = 2

    def __init__(self, response_type, embed=None, content=None, suggested=False):
        self.type = response_type
        self.embed = embed
        self.content = content
        self.init_suggested = suggested

    @property
    def is_mention(self):
        return self.embed is not None and self.content is not None
