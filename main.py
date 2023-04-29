import configparser
import pickle

import discord
import os

CONFIG = 'config.ini'
parser = configparser.ConfigParser()
try:
    parser.read(CONFIG)
    TOKEN = str(parser['DISCORD']['token'])
except:
    TOKEN = str(os.environ['token'])


intents = discord.Intents.all()

bot = discord.Bot(case_insensitive=True,
                      description="Simple betting bot to gamble on the outcome of admin created events.")  # , intents=intents)

@bot.event
async def on_ready():
    print('Connected to bot: {}'.format(bot.user.name))
    print('Bot ID: {}'.format(bot.user.id))

initial_extensions = (
    'betting',
    "signing",
)

for extension in initial_extensions:
  try:
    bot.load_extension(extension)
  except Exception as e:
    print(f'Failed to load extension {extension}.')




bot.run(TOKEN)