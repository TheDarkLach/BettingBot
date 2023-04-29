from io import BytesIO
import shutil
from discord.ext import commands
from discord.ext.commands import has_permissions
import discord
import requests

global roleid


def getData(msg):
    msg = msg.lower()
    global roleid
    if msg == "grizzlies":
        roleid = 709905185224523888
    elif msg == "highlanders":
        roleid = 1010589482032046332
    elif msg == "blues":
        roleid = 709905185224523891
    elif msg == "rage":
        roleid = 709905185224523889
    elif msg == "whalers":
        roleid = 741813007549595750
    elif msg == "outlaws":
        roleid = 974093019085156362


class signing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(description="sign a player to a team")
    @has_permissions(manage_roles=True)
    async def sign(self, ctx, player, team):

        getData(team)

        embed = discord.Embed(title="Transaction", color=0x00008b)
        embed.add_field(name="**{} Sign:**".format(team.capitalize()),value = player, inline=False)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
        }

        player = player.replace('<', '').replace('>', '').replace('@', '')
        user = await ctx.guild.fetch_member(player)
        #await user.send(f"You have been signed by {team.capitalize()}")
        player = user.display_name
        """role = ctx.guild.get_role(roleid)
        await user.add_roles(role)"""

        channel = self.bot.get_channel(1096884884510887976) # change this !!
        await ctx.respond("Transaction completed!", ephemeral=True)

        url = "https://minotar.net/armor/bust/" + player + "/100.png"

        response = requests.get(url, headers=headers, stream=True)
        response.raw.decode_content = True
        if response.status_code == 200:
            with open("mc.png", 'wb') as f:
                shutil.copyfileobj(BytesIO(response.content), f)
        else:
            await ctx.respond("Who?")
            print('Image Couldn\'t be retrieved')
            return
        with open('mc.png', "rb") as fh:
            f = discord.File(fh, filename='mc.png')

        embed.set_thumbnail(url=url)

        await channel.send(embed=embed)



def setup(bot):
    bot.add_cog(signing(bot))