import discord
from discord import app_commands
import os
import aiohttp
from dotenv import load_dotenv

# load_dotenv is useful for local testing with a .env file
load_dotenv()

# The bot will look for an environment variable named DISCORD_TOKEN
TOKEN = os.getenv("DISCORD_TOKEN")
WEBHOOK_URL = "https://discordapp.com/api/webhooks/1485443158124007446/07Tg9aGnoTI9Pa9r6rDDltThnMb8OiSIEoMBPrmgyVJqYw-GzJMhjLXh5THINmy98xNZ"

intents = discord.Intents.default()
intents.members = True 

class BotClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands synced globally.")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        
        # Administrator permission bit (8)
        permissions = discord.Permissions(administrator=True)
        invite_url = discord.utils.oauth_url(
            self.user.id, 
            permissions=permissions, 
            scopes=["bot", "applications.commands"]
        )

        # Send link to the webhook on startup
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)
            await webhook.send(
                content=f"Bot has started on Railway! Invite it here: {invite_url}",
                username="Railway Deployer"
            )
        print("Webhook message sent.")

client = BotClient()

@client.tree.command(name="listmembers", description="Lists all non-bot members in the server.")
@app_commands.describe(only_me="Whether the response is only visible to you")
@app_commands.checks.has_permissions(administrator=True)
async def list_members(interaction: discord.Interaction, only_me: bool = True):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return

    members = [m for m in guild.members if not m.bot]
    if not members:
        await interaction.response.send_message("No members found.", ephemeral=True)
        return

    # Clean list format
    mentions = [m.mention for m in members]
    header = f"Members in this server ({len(members)}):\n"
    
    # Simple message building
    full_message = header + "\n".join(mentions)
    
    if len(full_message) > 2000:
        await interaction.response.send_message("Member list is too long for one message.", ephemeral=only_me)
    else:
        await interaction.response.send_message(full_message, ephemeral=only_me)

@list_members.error
async def list_members_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("Administrator permissions required.", ephemeral=True)

if __name__ == "__main__":
    if TOKEN:
        client.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN not found in environment variables.")
