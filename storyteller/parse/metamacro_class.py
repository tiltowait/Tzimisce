"""metamacro-class.py - Defines a metamacro container class."""

class MetaMacro:
    """Container class that stores a context, command, and list of macros to perform."""

    def __init__(self, ctx, command, macros, handler):
        """
        Create a MetaMacro object.
        Args:
            ctx (discord.extensions.Context): A Discord bot context
            command (dict): A dictionary of command parameters
            macros (list[str]): A list of macro names to perform
            handler: A completion handler for macro results. Signature:
                     handler(command, ctx, send: bool)
        """
        self.ctx = ctx
        self.command = command
        self.macros = macros
        self.handler = handler


    async def run_next_macro(self):
        """
        Perform the next macro in the list. If the list is empty, it simply
        returns.
        Returns: Whatever the handler function returns.
        """
        if len(self.macros) == 0:
            return

        macro = self.macros.pop(0)
        self.command["syntax"] = macro
        self.command["comment"] = None
        return await self.handler(self.command, self.ctx, send=False)


    @property
    def is_done(self) -> bool:
        """True if there are no more macros left to run."""
        return len(self.macros) == 0


    @property
    def next_macro_name(self) -> bool:
        """Returns the name of the next macro to be run."""
        try:
            return self.macros[0]
        except IndexError:
            return None
