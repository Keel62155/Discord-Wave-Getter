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

    async def on_tree_error(self, interaction: discord.Interaction, error: Exception):
        print(f"[TREE ERROR] {error}")
        try:
            msg = f"Command error: `{error}`"
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except Exception:
            pass

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
async def list_members(interaction: discord.Interaction, only_me: bool = True):
    try:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.", ephemeral=True
            )
            return

        # Non-admins always get an ephemeral response regardless of only_me
        if not interaction.permissions.administrator:
            only_me = True

        # Defer immediately so Discord doesn't time out while fetching members
        await interaction.response.defer(ephemeral=only_me)

        try:
            members = [m async for m in guild.fetch_members(limit=None) if not m.bot]
        except (discord.Forbidden, discord.NotFound):
            await interaction.followup.send(
                "The bot needs to be **added to this server** to list its members.\n"
                "Have an admin invite it using the server install link.",
                ephemeral=True
            )
            return
        except Exception as e:
            await interaction.followup.send(
                f"Error fetching members: `{e}`", ephemeral=True
            )
            return

        if not members:
            await interaction.followup.send(
                "No non-bot members found in this server.", ephemeral=True
            )
            return

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

        for chunk in chunks:
            await interaction.followup.send(chunk, ephemeral=only_me)

    except Exception as e:
        print(f"[ERROR] list_members crashed: {e}")
        try:
            msg = f"Unexpected error: `{e}`"
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except Exception:
            pass

client.run(os.getenv("DISCORD_TOKEN"))