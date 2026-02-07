"""Example plugin demonstrating the plugin system."""

from aetherpackbot.core.context import Context
from aetherpackbot.plugins.base import Plugin, PluginMeta
from aetherpackbot.plugins.decorators import command


class EchoPlugin(Plugin):
    """Simple echo plugin for demonstration."""

    meta = PluginMeta(
        name="echo",
        version="1.0.0",
        description="Echo messages back to users",
        author="AetherPackBot Team",
    )

    async def on_load(self) -> None:
        """Called when plugin is loaded."""
        self.register_command(
            "echo",
            self.echo_command,
            description="Echo a message back",
            aliases=["say"],
        )

    @command(name="echo", description="Echo your message back")
    async def echo_command(self, ctx: Context) -> None:
        """Echo the user's message."""
        if ctx.args:
            message = " ".join(ctx.args)
            await ctx.reply(f"🔊 {message}")
        else:
            await ctx.reply("Usage: /echo <message>")

    @command(name="ping", description="Check bot responsiveness")
    async def ping_command(self, ctx: Context) -> None:
        """Respond with pong."""
        await ctx.reply("🏓 Pong!")

    async def on_message(self, context: Context) -> bool:
        """Handle general messages."""
        # Check for commands
        if context.is_command:
            cmd = context.command
            handler = self.get_command(cmd)
            if handler:
                await handler(context)
                return True
        return False
