from discord.ext import commands, tasks

message_counts = {}


class events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        #self.check_channel_task.start()

    """@tasks.loop(seconds=5)
    async def check_channel_task(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(1103469454161105017)
        if len(await channel.history(limit=2).flatten()) >= 2:
            messages = await channel.history(limit=2).flatten()
            await messages[1].delete()"""

    @commands.Cog.listener()
    async def on_message(self,message):
        channel = self.bot.get_channel(1103469454161105017)
        if message.channel == channel:
            if len(await channel.history(limit=2).flatten()) >= 2:
                messages = await channel.history(limit=2).flatten()
                await messages[1].delete()


def setup(bot):
    bot.add_cog(events(bot))
