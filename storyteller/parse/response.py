"""response.py - Describes Responses to user input."""

class Response:
    """Simple container class for parser response types."""
    # Response types
    POOL = 1
    TRADITIONAL = 2
    DATABASE = 3
    INITIATIVE = 4
    META_MACRO = 5

    def __init__(self, response_type, embed=None, content=None):
        self.type = response_type
        self.embed = embed
        self.content = content
        self.add_reaction = False

    @property
    def is_pool(self) -> bool:
        """True if response tyepe is a pool roll."""
        return self.type == Response.POOL

    @property
    def is_traditional(self) -> bool:
        """True if response tyepe is a tratitional roll."""
        return self.type == Response.TRADITIONAL

    @property
    def is_database(self) -> bool:
        """True if response tyepe is a database query."""
        return self.type == Response.DATABASE

    @property
    def is_initiative(self) -> bool:
        """True if response tyepe is an initiative query."""
        return self.type == Response.INITIATIVE

    @property
    def both_set(self) -> bool:
        """True if both the embed and content are set."""
        return self.embed is not None and self.content is not None

    def mentioned_content(self, author) -> str:
        """Returns the content with the author mentioned at the top."""
        if self.content:
            return f"{author.mention}\n{self.content}"
        return author.mention
