import discord
from discord import app_commands
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

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
        print("Slash commands synced")

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        
        # Permissions integer 8 for Administrator
        permissions = discord.Permissions(administrator=True)
        invite_url = discord.utils.oauth_url(
            self.user.id, 
            permissions=permissions, 
            scopes=["bot", "applications.commands"]
        )

        try:
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)
                await webhook.send(
                    content=f"Bot is online. Invite link: {invite_url}",
                    username="Railway Bot"
                )
        except Exception as e:
            print(f"Webhook failed: {e}")

client = BotClient()

@client.tree.command(name="listmembers", description="Lists all non-bot members")
@app_commands.describe(only_me="Hide the response from others")
@app_commands.checks.has_permissions(administrator=True)
async def list_members(interaction: discord.Interaction, only_me: bool = True):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("Use this in a server.", ephemeral=True)
        return

    members = [m for m in guild.members if not m.bot]
    if not members:
        await interaction.response.send_message("No members found.", ephemeral=True)
        return

    mentions = [m.mention for m in members]
    header = f"Members in this server ({len(members)}):\n"
    output = header + "\n".join(mentions)

    if len(output) > 2000:
        await interaction.response.send_message("List is too long.", ephemeral=only_me)
    else:
        await interaction.response.send_message(output, ephemeral=only_me)

@list_members.error
async def list_members_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("Administrator permission required.", ephemeral=True)

if __name__ == "__main__":
    if TOKEN:
        client.run(TOKEN)
    else:
        print("CRASH PREVENTED: DISCORD_TOKEN not found in Railway Variables.")
