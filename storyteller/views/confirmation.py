"""confirmation_view.py - A simple confirmation view."""

import discord
from discord.ui import Button


class Confirmation(discord.ui.View):
    """Presents an Okay/Cancel button pair."""

    def __init__(self, confirmation_style=discord.ButtonStyle.primary):
        super().__init__()
        self.confirmed = False

        confirm = Button(label="Confirm", style=confirmation_style)
        confirm.callback = self.confirm

        self.add_item(confirm)


    #@discord.ui.button(label="Confirm", style=self.confirmation_style)
    async def confirm(self, interaction: discord.Interaction):
        """Confirm the whatever-it-is."""
        await interaction.response.pong()
        await self._disable(interaction)
        self.confirmed = True
        self.stop()


    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, _, interaction: discord.Interaction):
        """Cancel the whatever-it-is."""
        await interaction.response.pong()
        await self._disable(interaction)
        self.confirmed = False
        self.stop()


    async def _disable(self, interaction):
        """Disable all buttons."""
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(view=self)
