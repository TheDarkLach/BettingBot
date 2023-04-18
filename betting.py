# Imports
import discord
from discord.ext import commands, tasks

import configparser
from datetime import timedelta, date, datetime

import pickle
import os

from discord.ui import View

################################################
# Setup

CONFIG = 'config.ini'
parser = configparser.ConfigParser()
try:
    parser.read(CONFIG)
    TOKEN = str(parser['DISCORD']['token'])
    TIMEZONE = str(parser['DISCORD']['timezone'])
    DAILY = int(parser['DISCORD']['daily'])
    STARTING_MONEY = int(parser['DISCORD']['starting_money'])
except:
    TOKEN = str(os.environ['token'])
    TIMEZONE = str(os.environ['timezone'])
    DAILY = int(os.environ['daily'])
    STARTING_MONEY = int(os.environ['starting_money'])


################################################
# Classes

class BettingSystem():
    def __init__(self):
        self._users = {}
        self._curr_events = {}
        self._past_events = {}
        self._eventIds = 0
        self._valid_yes = ["outlaws", "highlanders", "whalers", "grizzlies", "blues", "rage"]
        self._invalid_side_message = "result must be one of " + str(self._valid_yes)
        self.MAX_BET = 100000
        self.MIN_BET = 1

    # todo remove
    def clear(self):
        self._past_events = {}
        for key in self._users:
            user = self._users[key]
            user._past_bets = []
        return "Cleared all historical data. PnL and money remains."

    def add_event(self, team1, team2, odds=2.00):
        a = datetime.now()
        b = a + timedelta(hours=1)
        event = BetEvent(self.next_event_id(), team1, team2, odds, description=team1 + " VS " + team2)
        self._curr_events[event._id] = event
        embed = discord.Embed(title=event.information(), description=f"ID: {str(event._id)}",timestamp=b, color=0x00008b)
        embed.set_footer(text="\u200b Ending: ")
        return event._id, embed

    def resolve_event(self, event_id, result):
        if not (event_id in self._curr_events):
            return "Invalid eventId, try using <ongoing> to see current events."

        event = self._curr_events.pop(event_id)
        event.payout(result)
        self._past_events[event_id] = event
        return event.information(True)

    def lock_event(self, event_id):
        if not (event_id in self._curr_events):
            return "Invalid eventId, try using <ongoing> to see current events."
        if self._curr_events[event_id].locked():
            return self._curr_events[event_id]._description + " is already locked."
        return self._curr_events[event_id].lock()

    def unlock_event(self, event_id):
        if not (event_id in self._curr_events):
            return "Invalid eventId, try using <ongoing> to see current events."
        if not (self._curr_events[event_id].locked()):
            return self._curr_events[event_id]._description + " is not locked."
        return self._curr_events[event_id].unlock()

    def next_event_id(self):
        self._eventIds += 1
        return self._eventIds

    def update_max_bet(self, max_bet):
        if max_bet < self.MIN_BET:
            return "The maximum bet must be greater than the minimum bet."
        self.MAX_BET = max_bet
        return "Maximum bet updated to " + str(max_bet) + "."

    def cancel_bet(self, user_id, event_id):
        if not (event_id in self._curr_events):
            return "Invalid eventId, try using <ongoing> to see current events."
        if not user_id in self._users:
            return "That user does not have any current bets."
        user = self._users[user_id]
        event = self._curr_events[event_id]
        # remove from event bets list
        for bet in list(event._bets):
            if bet.user()._id == user._id:
                event._bets.remove(bet)
                # for bet in user._current_bets:
                #     if bet._underlying._id == event_id:
                user._current_bets.remove(bet)
                user._money += bet.amount()
        return user.name() + "'s bets on " + str(event_id) + " have been deleted."

    def list_current_events(self):
        output = ""
        for key in self._curr_events:
            event = self._curr_events[key]
            output += "<" + str(event._id) + "> " + event.information() + "\n"
        if output == "":
            output = "No ongoing events."
        return output

    def list_past_events(self):
        output = ""
        for key in self._past_events:
            event = self._past_events[key]
            output += "<" + str(event._id) + "> " + event.information() + "\n"
        if output == "":
            output = "No past events."
        return output

    def user_bet(self, event_id, user, team, amount):
        if not user.id in self._users:
            self._users[user.id] = User(user.display_name, user.id)

        person = self._users[user.id]
        if not person.has_money(amount):
            return person.name() + " does not have enough money for that bet! You have " + "$" + "{:.2f}".format(
                person.money()) + "."

        if amount > self.MAX_BET:
            return person.name() + " that amount is above the maximum of " + "$" + "{:.2f}".format(self.MAX_BET) + "."

        if amount < self.MIN_BET:
            return person.name() + " that amount is below the minimum of " + "$" + "{:.2f}".format(self.MIN_BET) + "."

        if not event_id in self._curr_events:
            return person.name() + " that event could not be found."

        if self._curr_events[event_id].locked():
            return person.name() + " that event is closed for betting."

        if team != self._curr_events[event_id]._team1 and team != self._curr_events[event_id]._team2:
            return person.name() + " " + self._invalid_side_message

        return self._curr_events[event_id].add_bet(person, amount, team)

    def list_user_bets(self, user):
        if not user.id in self._users:
            self._users[user.id] = User(user.display_name, user.id)

        person = self._users[user.id]
        return person.list_bets()

    def list_user_past_bets(self, user):
        if not user.id in self._users:
            self._users[user.id] = User(user.display_name, user.id)

        person = self._users[user.id]
        return person.list_past_bets()

    def list_money_leaderboard(self):
        output = "LEADERBOARD ($):\n"
        i = 1
        users_sorted_by_money = sorted(self._users.items(), key=lambda x: x[1].money_including_ongoing(), reverse=True)
        for (_id, user) in users_sorted_by_money:
            output += f"{str(i): >{2}}" + ". " + f"{user.name(): <{20}}" + " $" + f"{user.money_including_ongoing(): <20.2f}\n"
            i += 1
        return output

    def list_best_pnl(self):
        output = "LEADERBOARD (PnL):\n"
        i = 1
        users_sorted_by_money = sorted(self._users.items(), key=lambda x: x[1].pnl(), reverse=True)
        for (_id, user) in users_sorted_by_money:
            neg = " "
            if user.pnl() < 0:
                neg = "-"
            output += f"{str(i): >{2}}" + ". " + f"{user.name(): <{20}} " + neg + "$" + f"{abs(user.pnl()): <20.2f}\n"
            i += 1
        return output

    def print_money(self, user):
        if not user.id in self._users:
            self._users[user.id] = User(user.display_name, user.id)

        person = self._users[user.id]
        return person.print_money()

    def daily(self, user):
        if not user.id in self._users:
            self._users[user.id] = User(user.display_name, user.id)

        person = self._users[user.id]
        return person.daily()

    def rename_user(self, user):
        if not user.id in self._users:
            self._users[user.id] = User(user.display_name, user.id)

        person = self._users[user.id]
        return person.rename(user.display_name)


def custom_format(td):
    minutes, _seconds = divmod(td.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return '{:d}hr {:02d}m'.format(hours, minutes)


class User():
    def __init__(self, name, userId):
        self._id = userId
        self._name = name
        self._money = STARTING_MONEY
        self._current_bets = []
        self._past_bets = []
        self._daily = self._today() - timedelta(days=1)
        self._total_pnl = 0

    def name(self):
        return self._name

    def rename(self, name):
        self._name = name
        return name + " was renamed successfully."

    def pnl(self):
        return self._total_pnl

    def money(self):
        return self._money

    def money_including_ongoing(self):
        return sum([bet._amount for bet in self._current_bets]) + self.money()

    def mention(self):
        return "<@" + str(self._id) + ">"

    def print_money(self):
        return self.name() + " has " + "$" + "{:.2f}".format(self.money()) + "."

    def list_bets(self):
        neg = ""
        if self._total_pnl < 0:
            neg = "-"
        output = self.name() + " has total PnL " + neg + "${:.2f}".format(abs(self._total_pnl)) + ".\n"
        if len(self._current_bets) > 0:
            output += "Live bets:\n"
        else:
            output += "No current bets.\n"
        for bet in self._current_bets:
            output += "\t" + bet.description() + "\n"
        return output

    def list_past_bets(self):
        neg = ""
        if self._total_pnl < 0:
            neg = "-"
        output = self.mention() + " has total PnL " + neg + "${:.2f}".format(
            abs(self._total_pnl)) + ".\n```Past bets:\n"
        for bet in self._past_bets:
            output += "\t" + bet.description() + "\n"
        return output + "```"

    def archive_bet(self, event_id):
        i = 0
        for bet in self._current_bets:
            if bet._underlying._id == event_id:
                self._past_bets.append(self._current_bets.pop(i))
            i += 1
        return

    def _today(self):
        dt = datetime.today()
        return datetime(dt.year, dt.month, dt.day)

    def daily(self):
        if self._today() - self._daily < timedelta(days=1):
            return self.name() + " you need to wait " + custom_format(
                timedelta(days=1) - (datetime.today() - self._daily)) + " more to retrieve your daily reward!"
        self._money += abs(DAILY)
        self._daily = self._today()
        return self.name() + " gained ${:.2f}".format(abs(DAILY))

    def has_money(self, amount):
        return self._money >= amount

    def win_bet(self, amount, odds):
        self._money += amount * odds
        self._total_pnl += amount * (odds - 1)

    def lose_bet(self, amount):
        self._total_pnl -= amount

    def place_bet(self, betEvent, amount, side):
        assert (self.has_money(amount))
        bet = Bet(betEvent, self, amount, side)
        self._money -= amount
        self._current_bets.append(bet)
        return bet


class BetEvent():
    def __init__(self, eventId, team1,team2, odds,description):
        self._id = eventId
        self._team1 = team1
        self._team2 = team2
        self._bets = []
        self._odds = odds  # odds for "yes"
        self._resolved = False
        self._result = "n/a"
        self._locked = False
        self._description = description

    def add_bet(self, user, amount, side):
        if user.has_money(amount):
            self._bets.append(user.place_bet(self, amount, side))
            return user.name() + "'s $" + "{:.2f}".format(amount) + " bet placed successfully."
        else:
            return "insufficient funds " + user.name() + "!"

    def payout(self, winning_side):
        self._resolved = True
        self._locked = True
        self._result = winning_side
        print(winning_side)

        for bet in self._bets:
            bet.resolve(winning_side, self.odds(bet.side()))
            bet.user().archive_bet(bet._underlying._id)

    def resolved(self):
        return self._resolved

    def odds(self, side):
        if side:
            return self._odds
        return self._odds / (self._odds - 1)  # x/(x-1) is the other side

    def information(self, mention=False):
        output = ""
        if mention:
            output = "```"

        locked = ""
        if self.locked() and not (self.resolved()):
            locked = " (locked)"
        output += self._team1 + " VS " + self._team2 + " @ $" + "{:.2f}".format(self.odds(True)) + locked + "\n"
        if self.resolved():
            output += "RESULT: " + str(self._result).upper() + "\n"
        if mention:
            output += "```"
        for bet in self._bets:
            output += "\t" + bet.short_info(mention) + "\n"
        return output

    def locked(self):
        return self._locked

    def lock(self):
        if self._locked:
            return "Already locked."
        else:
            self._locked = True
            return "Event " + str(self._id) + " locked. Bets are now closed."

    def unlock(self):
        if not (self._locked):
            return "Already unlocked."
        if self._resolved:
            return "Already resolved - can't unlock."
        else:
            self._locked = False
            return "Event " + str(self._id) + " unlocked. Bets are now reopened."


class Bet():
    def __init__(self, event, user, amount, side):
        self._underlying = event
        self._user = user
        self._amount = amount
        self._side = side
        self._resolution = "n/a"

    def description(self):
        join = " that "
        if not (self.side()):
            join = " against "
        if self._resolution == "n/a":
            return self.user().name() + " bet " + "$" + "{:.2f}".format(self.amount()) + " @ $" + "{:.2f}".format(
                self.underlying().odds(self.side())) + join + str(self._side) + " wins"
        else:
            return self.user().name() + " " + self._resolution + " " + "$" + "{:.2f}".format(
                self.winnings()) + " betting" + join + self.underlying()._description

    def short_info(self, mention=False):

        name = self.user().name()
        if mention:
            name = self.user().mention()

        if self._resolution == "n/a":
            return self.user().name() + " bet " + "$" + "{:.2f}".format(self.amount())
        else:
            return name + " " + self._resolution + " " + "$" + "{:.2f}".format(self.winnings())

    def winnings(self):
        if self._resolution != "won":
            return self._amount
        return self.amount() * (self._underlying.odds(self.side()))

    def resolve(self, outcome, odds):
        if self._resolution != "n/a":
            raise Exception("oops - double resolve bet")

        if outcome == self.side():
            self._resolution = "won"
            self._user.win_bet(self.amount(), odds)
        else:
            self._resolution = "lost"
            self._user.lose_bet(self.amount())

    def side(self):
        return self._side

    def amount(self):
        return self._amount

    def user(self):
        return self._user

    def underlying(self):
        return self._underlying


class MyModal(discord.ui.Modal):
    def __init__(self, team,id,betting_system, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(discord.ui.InputText(label="Bet Amount", placeholder="0.00"))
        self.result = team
        self.id = id
        self.betting_system = betting_system


    async def callback(self, interaction: discord.Interaction):
        #await interaction.response(wrap(self.bot.system.user_bet(int(self.event_id), interaction.user, self.result, float(self.children[0].value))), ephemeral=True)
        #await interaction.response.send_message(f"you bet ${self.children[0].value}", ephemeral=True)
        #await interaction.response.send_message(BettingSystem.user_bet(int(self.id), interaction.user, self.result, float(self.children[0].value)), ephemeral=True)
        result = self.betting_system.user_bet(self.id, interaction.user, self.result, float(self.children[0].value))
        await interaction.response.send_message(result, ephemeral=True)

# wraps the text in ```<text>``` for ascii table output
def wrap(text):
    return "```" + text + "```"

PICKLE_FILENAME = 'betting_system.pickle'
class betting(commands.Cog):
    def __init__(self, bot):
      self.bot = bot
      self.autosave.start()
      #### PICKLE (object persistence)
      try:
          with open(PICKLE_FILENAME, 'rb') as handle:
              bot.system = pickle.load(handle)
          print("Successfully loaded " + PICKLE_FILENAME)
      except:
          print("Couldn't find pickle file " + PICKLE_FILENAME)
          bot.system = BettingSystem()


    def getEmoji(self,team):
        team = team.lower()
        if team == "outlaws":
            return "<:VAN:1097742618441560075>"
        if team == "highlanders":
            return "<:HFX:1097742653103288430>"
        if team == "blues":
            return "<:SAS:1097742592814362664>"
        if team == "whalers":
            return "<:HFD:1097742654151868587>"
        if team == "rage":
            return "<:CAS:1097742655837974580>"
        if team == "grizzlies":
            return "<:ANC:1097742565190668338>"
        return "fuck if i know"
    
    ################################################
    # BETTING
    
    # Create event
    """@discord.slash_command(aliases=["g"], usage="<odds> <team1> <team2>",
                    help="Allows a Manager to create an event for users to bet on.\ne.g. game 2 outlaws highlanders")
    @commands.has_role("Manager")
    async def game(self,ctx, odds, team1,team2):
        await ctx.respond(embed=self.bot.system.add_event(team1,team2, float(odds)))"""

    @discord.slash_command(aliases=["g"], usage="<odds> <team1> <team2>",
                           help="Allows a Manager to create an event for users to bet on.\ne.g. game 2 outlaws highlanders")
    @commands.has_role("Manager")
    async def game(self, ctx, odds, team1, team2):


        temp = self.bot.system.add_event(team1, team2, float(odds))
        id = temp[0]
        send = temp[1]

        button1 = discord.ui.Button(custom_id=f"button-1-{id}", style=discord.ButtonStyle.primary,
                                    emoji=self.getEmoji(team1))
        button2 = discord.ui.Button(custom_id=f"button-2-{id}", style=discord.ButtonStyle.primary,
                                    emoji=self.getEmoji(team2))

        async def on_timeout():
            await ctx.respond("You didn't bet in time!", ephermal=True)

        view = View(timeout=3600)
        view.add_item(button1)
        view.add_item(button2)

        await ctx.respond(embed=send,view=view)
        async def callback1(interaction):
            self.team = team1
            await interaction.response.send_modal(MyModal(title="betting", team=team1, id=id,betting_system=self.bot.system))
        async def callback2(interaction):
            self.team = team2
            await interaction.response.send_modal(MyModal(title="betting",team=team2, id=id,betting_system=self.bot.system))

        button1.callback = callback1
        button2.callback = callback2

    
    
    # Resolve event
    @discord.slash_command(aliases=["r"], usage="<eventId> <result",
                    help="Allows a Manager to resolve an event that users have bet on.\ne.g. resolve 1 outlaws")
    @commands.has_role("Manager")
    async def resolve(self, ctx, event_id, result):
        await ctx.respond(self.bot.system.resolve_event(int(event_id), result))
    
    
    # Bet on an event
    @discord.slash_command(aliases=["b"], usage="<eventId> <result (yes/no)> <amount>",
                    help="Allows any user to bet on an ongoing event.\ne.g. bet 1 y 100.")
    async def bet(self, ctx, event_id, result, amount):
        await ctx.respond(wrap(self.bot.system.user_bet(int(event_id), ctx.author, result, float(amount))),ephemeral=True)
    
    
    # Lock an event
    @discord.slash_command(aliases=["lo"], usage="<eventId>", help="Allows a Manager to lock a current event.\ne.g. lock 11.")
    @commands.has_role("Manager")
    async def lock(self, ctx, event_id):
        await ctx.respond(wrap(discord.system.lock_event(int(event_id))))
    
    
    # Unlock an event
    @discord.slash_command(aliases=["unlo"], usage="<eventId>",
                    help="Allows a Manager to unlock a current event.\ne.g. unlock 11.")
    @commands.has_role("Manager")
    async def unlock(self, ctx, event_id):
        await ctx.respond(wrap(self.bot.system.unlock_event(int(event_id))))
    
    
    ################################################
    # See current money
    @discord.slash_command(aliases=["m"], usage="", help="Allows any user to see their current money supply.")
    async def money(self, ctx):
        await ctx.respond(wrap(self.bot.system.print_money(ctx.author)))
    
    
    # Get daily money reward
    @discord.slash_command(aliases=["d"], usage="", help="Retrieve daily login reward.")
    async def daily(self, ctx):
        await ctx.respond(wrap(self.bot.system.daily(ctx.author)))
    
    
    ################################################
    # System information
    
    # list all ongoing events
    @discord.slash_command(aliases=["list", "o", "on", "live"], usage="", help="Allows any user to see all live events and bets.")
    async def ongoing(self, ctx):
        await ctx.respond(wrap(self.bot.system.list_current_events()))
    
    
    # list all past events
    @discord.slash_command(aliases=["pastevents", "past", "all"], usage="",
                    help="Allows any user to see all past events and bets.")
    async def allhistory(self, ctx):
        await ctx.respond(wrap(self.bot.system.list_past_events()))
    
    
    # list a users current bets
    @discord.slash_command(aliases=["bs"], usage="", help="Allows any user to see their current bets.")
    async def bets(self, ctx):
        await ctx.respond(wrap(self.bot.system.list_user_bets(ctx.author)))
    
    
    # cancel a user's current bets for a particular event
    @discord.slash_command(aliases=["can"], usage="<@user> <event_id>", help="Allows a Manager to cancel someone's bets.")
    @commands.has_role("Manager")
    async def cancel(self, ctx, user, event_id):
        user = user.replace('<', '').replace('>', '').replace('@', '')
        await ctx.respond(wrap(self.bot.system.cancel_bet(int(user), int(event_id))))
    
    
    # A user's betting history
    @discord.slash_command(aliases=["h", "hist"], usage="", help="Allows any user to see their past betting history.")
    async def history(self, ctx):
        await ctx.respond(self.bot.system.list_user_past_bets(ctx.author))
    
    
    # Leaderboard ranked by money
    @discord.slash_command(aliases=["top", "leader", "l"], usage="", help="Ranks everyone by money.")
    async def leaderboard(self, ctx):
        await ctx.respond(wrap(self.bot.system.list_money_leaderboard()))
    
    
    # Leaderboard ranked by PnL
    @discord.slash_command(aliases=["allpnl", "pnl", "p"], usage="", help="Ranks everyone by profit/loss.")
    async def bestpnl(self, ctx):
        await ctx.respond(wrap(self.bot.system.list_best_pnl()))
    
    
    # Store all user data (serialized)
    @discord.slash_command(aliases=["s", "shutdown"], usage="", help="Save current system state to file.")
    async def save(self, ctx):
        with open(PICKLE_FILENAME, 'wb') as handle:
            pickle.dump(self.bot.system, handle, protocol=pickle.HIGHEST_PROTOCOL)
        await ctx.respond(wrap("Data saved successfully."))
        with open(PICKLE_FILENAME, 'rb') as handle:
            await ctx.respond(file=discord.File(handle))
    
    
    # Load user data (serialized)
    @discord.slash_command(aliases=["reload"], usage="",
                    help="Load current system state from file. Must be attached with the command and named " + PICKLE_FILENAME + ".")
    @commands.has_role("Manager")
    async def load(self, ctx):
        if not (ctx.message.attachments):
            await ctx.respond(wrap(ctx.author.display_name + " loading requires an attachment."))
            return
        for attachment in ctx.message.attachments:
            if attachment.filename == PICKLE_FILENAME:
                file_bytes = await attachment.read()
                self.bot.system = pickle.loads(file_bytes)
                await ctx.respond(wrap("file loaded successfully."))
                return
    
    
    @discord.slash_command(aliases=["latency"], usage="", help="Show self.bot latency.")
    async def ping(self, ctx):
        await ctx.respond(wrap(str(round(self.bot.latency * 1000, 2)) + "ms"))
    
    
    
    # renaming users
    @discord.slash_command(usage="", help="Regenerate a users' name (using their current display name).")
    async def rename(self, ctx):
        await ctx.respond(wrap(self.bot.system.rename_user(ctx.author)))
    
    
    # Update max bet
    @discord.slash_command(aliases=["max"], usage="<eventId>", help="Allows a Manager to update the maximum betting amount.")
    @commands.has_role("Manager")
    async def max_bet(self, ctx, maxbet):
        await ctx.respond(wrap(self.bot.system.update_max_bet(int(maxbet))))
    
    
    # Clear history
    @discord.slash_command(aliases=["clear_past"], usage="",
                    help="Allows a Manager to clear past events (lowers save space).")
    @commands.has_role("Manager")
    async def clear(self, ctx):
        await ctx.respond(wrap(self.bot.system.clear()))

    @tasks.loop(hours=24)
    async def autosave(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(1097702157966393404)
        with open(PICKLE_FILENAME, 'wb') as handle:
            pickle.dump(self.bot.system, handle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(PICKLE_FILENAME, 'rb') as handle:
            await channel.send(datetime.now(),file=discord.File(handle))

def setup(bot):
    bot.add_cog(betting(bot))