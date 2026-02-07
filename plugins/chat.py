"""Chat plugin for AI-powered conversations."""

from aetherpackbot.core.context import Context
from aetherpackbot.plugins.base import Plugin, PluginMeta
from aetherpackbot.plugins.decorators import command
from aetherpackbot.providers.base import ChatMessage, ChatRole


class ChatPlugin(Plugin):
    """AI chat plugin using configured LLM providers."""

    meta = PluginMeta(
        name="chat",
        version="1.0.0",
        description="AI-powered chat functionality",
        author="AetherPackBot Team",
    )

    def __init__(self) -> None:
        super().__init__()
        self.system_prompt = "You are a helpful assistant."

    async def on_load(self) -> None:
        """Register commands."""
        self.register_command("chat", self.chat_command)
        self.register_command("ask", self.chat_command, aliases=["ai"])

    @command(name="chat", description="Chat with AI")
    async def chat_command(self, ctx: Context) -> None:
        """Handle chat command."""
        if not ctx.args:
            await ctx.reply("Usage: /chat <your message>")
            return

        if not self.engine:
            await ctx.reply("Engine not available")
            return

        provider = self.engine.get_default_provider()
        if not provider:
            await ctx.reply("No LLM provider configured")
            return

        # Send typing indicator
        await ctx.reply_typing()

        # Build messages
        user_message = " ".join(ctx.args)
        messages = [
            ChatMessage(role=ChatRole.SYSTEM, content=self.system_prompt),
            ChatMessage(role=ChatRole.USER, content=user_message),
        ]

        try:
            response = await provider.chat(messages)
            await ctx.reply(response.content)
        except Exception as e:
            await ctx.reply(f"Error: {str(e)}")

    @command(name="setprompt", description="Set system prompt")
    async def set_prompt_command(self, ctx: Context) -> None:
        """Set the system prompt."""
        if not ctx.args:
            await ctx.reply(f"Current prompt: {self.system_prompt}")
            return

        self.system_prompt = " ".join(ctx.args)
        await ctx.reply("System prompt updated!")

    async def on_message(self, context: Context) -> bool:
        """Handle messages."""
        if context.is_command:
            cmd = context.command
            handler = self.get_command(cmd)
            if handler:
                await handler(context)
                return True
        return False
