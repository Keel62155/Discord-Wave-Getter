import discord
from discord import app_commands
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.members = True 

class BotClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.webhook_url = "https://discordapp.com/api/webhooks/1485443158124007446/07Tg9aGnoTI9Pa9r6rDDltThnMb8OiSIEoMBPrmgyVJqYw-GzJMhjLXh5THINmy98xNZ"

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands synced globally.")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        
        # Request Administrator permission (Integer 8)
        permissions = discord.Permissions(administrator=True)
        
        # Generate the OAuth2 invite URL
        invite_url = discord.utils.oauth_url(
            self.user.id, 
            permissions=permissions, 
            scopes=["bot", "applications.commands"]
        )

        # Send the link to the webhook
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(self.webhook_url, session=session)
            await webhook.send(
                content=f"Bot is online. Use this link to invite with Administrator permissions:\n{invite_url}",
                username="Bot Status Logger"
            )
        
        print("Invite URL has been sent to the webhook.")

client = BotClient()

@client.tree.command(
    name="listmembers",
    description="Lists all non-bot members in the server.",
)
@app_commands.describe(only_me="Whether the response is only visible to you (default: True)")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
async def list_members(interaction: discord.Interaction, only_me: bool = True):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "This command can only be used inside a server.", ephemeral=True
        )
        return

    # If the bot isn't a member of this server it can't access the member list
    if guild.me is None:
        await interaction.response.send_message(
            "The bot needs to be **added to this server** to list its members.\n"
            "Have an admin invite it using the server install link.",
            ephemeral=True
        )
        return

    members = [m for m in guild.members if not m.bot]

    if not members:
        await interaction.response.send_message(
            "No non-bot members found in this server.", ephemeral=True
        )
        return

    # Removed the asterisk as requested in your preferences
    mentions = [f"{m.mention}" for m in members]

    header = f"Members in this server ({len(members)}):\n"
    chunks = []
    current = header

    for mention in mentions:
        line = mention + "\n"
        if len(current) + len(line) > 2000:
            chunks.append(current.rstrip())
            current = line
        else:
            current += line

    if current.strip():
        chunks.append(current.rstrip())

    await interaction.response.send_message(chunks[0], ephemeral=only_me)
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk, ephemeral=only_me)

@list_members.error
async def list_members_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "You need the Administrator permission to use this command.", ephemeral=True
        )

client.run(os.getenv("DISCORD_TOKEN"))