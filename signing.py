from io import BytesIO
import shutil

from discord import option
from discord.ext import commands
from discord.ext.commands import has_permissions
import discord
import requests


def getData(msg):
    team = msg.lower()
    if team == "grizzlies":
        return 709905185224523888
    if team == "bandits":
        return 1111389039489187980
    if team == "outlaws":
        return 974093019085156362
    if team == "blues":
        return 709905185224523891
    if team == "spartans":
        return 741813007549595750
    if team == "redwolves":
        return 1111392124961816599
    if team == "rage":
        return 709905185224523889
    if team == "hitmen":
        return 1111377574023676064
    if team == "storm":
        return 1010589482032046332
    return "fuck if i know"


class signing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(description="sign a player to a team")
    @has_permissions(manage_roles=True)
    @option("team", description="Choose the team",
            choices=["Grizzlies", "Bandits", "Outlaws", "Blues", "Spartans", "Redwolves", "Hitmen", "Storm"])
    async def sign(self, ctx, player, team):

        roleid = getData(team)

        embed = discord.Embed(title="Transaction", color=0x00008b)
        embed.add_field(name="**{} Sign:**".format(team.capitalize()),value = player, inline=False)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
        }

        player = player.replace('<', '').replace('>', '').replace('@', '')
        user = await ctx.guild.fetch_member(player)
        #await user.send(f"You have been signed by {team.capitalize()}")
        player = user.display_name
        role = ctx.guild.get_role(roleid)
        await user.add_roles(role)


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

        await ctx.respond(embed=embed)

    @discord.slash_command(description="release a player from a team")
    @has_permissions(manage_roles=True)
    @option("team", description="Choose the team",
            choices=["Grizzlies", "Bandits", "Outlaws", "Blues", "Spartans", "Redwolves", "Hitmen", "Storm"])
    async def release(self, ctx, player, team):

        roleid = getData(team)

        embed = discord.Embed(title="Transaction", color=0x00008b)
        embed.add_field(name="**{} Release:**".format(team.capitalize()), value=player, inline=False)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
        }

        player = player.replace('<', '').replace('>', '').replace('@', '')
        user = await ctx.guild.fetch_member(player)
        # await user.send(f"You have been signed by {team.capitalize()}")
        player = user.display_name
        role = ctx.guild.get_role(roleid)
        await user.remove_roles(role)

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

        await ctx.respond(embed=embed)



def setup(bot):
    bot.add_cog(signing(bot))