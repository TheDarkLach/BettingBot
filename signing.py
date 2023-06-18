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
        return "<:ANC:974426032591487046>"
    if team == "bandits":
        return "<:HOU:710972511558303914>"
    if team == "outlaws":
        return "<:VAN:761247825795219466>"
    if team == "blues":
        return "<:SAS:1111371453544288348>"
    if team == "spartans":
        return "<:SJS:1111376173621055629>"
    if team == "redwolves":
        return "<:WSH:1111392076358226100>"
    if team == "rage":
        return "<:CAS:1084273779657687101>"
    if team == "hitmen":
        return "<:SUR:819294775999725589>"
    if team == "storm":
        return "<:ORL:761247932598845480>"
    return "fuck if i know"


class signing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(description="sign a player to a team")
    @has_permissions(manage_roles=True)
    @option("team", description="Choose the team",
            choices=["Grizzlies", "Bandits", "Outlaws", "Blues", "Spartans", "Redwolves", "Hitmen", "Storm"])
    async def sign(self, ctx, player, team):

        emoji = getData(team)

        embed = discord.Embed(title=f"{emoji} Transaction", color=0x00008b)
        embed.add_field(name="**{} Sign:**".format(team.capitalize()),value = player, inline=False)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
        }


        #user = await ctx.guild.fetch_member(player)
        #await user.send(f"You have been signed by {team.capitalize()}")
        #role = ctx.guild.get_role(roleid)
        #await user.add_roles(role)
        await ctx.respond("One second!", ephemeral=True)


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

        await ctx.channel.send(embed=embed)

    @discord.slash_command(description="release a player from a team")
    @has_permissions(manage_roles=True)
    @option("team", description="Choose the team",
            choices=["Grizzlies", "Bandits", "Outlaws", "Blues", "Spartans", "Redwolves", "Hitmen", "Storm"])
    async def release(self, ctx, player, team):

        emoji = getData(team)

        embed = discord.Embed(title=f"{emoji} Transaction", color=0x00008b)
        embed.add_field(name="**{} Release:**".format(team.capitalize()), value=player, inline=False)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
        }


        #user = await ctx.guild.fetch_member(player)
        # await user.send(f"You have been signed by {team.capitalize()}")
        #role = ctx.guild.get_role(roleid)
        #await user.remove_roles(role)
        await ctx.respond("One second!", ephemeral=True)

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

        await ctx.channel.send(embed=embed)



def setup(bot):
    bot.add_cog(signing(bot))
