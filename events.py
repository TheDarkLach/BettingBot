import discord
import pytz
from discord.ext import commands, tasks
import datetime
import asyncio
import betting



class events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.check_messages())

    async def check_messages(self):
        sent_users = set()  # Keep track of users who have been sent a message
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            # Check for messages sent in the last 10 minutes
            for channel in self.bot.get_all_channels():
                if isinstance(channel, discord.TextChannel):
                    async for message in channel.history(limit=None):
                        user = message.author
                        if (datetime.datetime.now(pytz.utc) - message.created_at).total_seconds() <= 600 and not user.bot and user not in sent_users:
                            # Send a message to the user who sent the message
                            #await user.send("You have been active! Keep it up!")
                            user.User.add_money()
                            #print("added money to: " + str(user.id))
                            sent_users.add(user)

            # Wait for 10 minutes before checking messages again
            await asyncio.sleep(10)
            sent_users.clear()


def setup(bot):
    bot.add_cog(events(bot))
