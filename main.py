import discord
from dotenv import load_dotenv
import os

intents = discord.Intents.default()
bot = discord.Bot(intents = intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is online.")

@bot.slash_command(name = "ping", description = "Check the bots ping")
async def ping(ctx):
    await ctx.respond(f"{bot.latency * 1000}ms")

load_dotenv()
bot.run(os.getenv("TOKEN"))