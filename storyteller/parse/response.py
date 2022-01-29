"""response.py - Describes Responses to user input."""

class Response:
    """Simple container class for parser response types."""

    # Response types
    POOL = 1 # Pool-based rolls
    TRADITIONAL = 2 # Traditional rolls
    DATABASE = 3 # RollDB response
    INITIATIVE = 4 # Initiative response
    META_MACRO = 5 # Metamacro response


    def __init__(self, response_type, embed=None, content=None):
        """
        Create a basic Response object.
        Args:
            response_type (int): The type of response being created
            embed (Optional[discord.Embed]): The embed to present to the user
            content (Optional[str]): The string to present to the user
        A Response can contain both an embed and content string.
        """
        self.type = response_type
        self.embed = embed
        self.content = content
        self.add_reaction = False
        self.ephemeral = False


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


    def mentioned_content(self, user) -> str:
        """
        Returns the content with the user mentioned at the top.
        Args:
            user: The Discord user to mention
        Returns (str): The content with a Discord mention at the top
        """
        if self.content:
            return f"{user.mention}\n{self.content}"
        return user.mention
