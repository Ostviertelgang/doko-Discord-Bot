import datetime

import discord
import requests
import json
from discord.ext import commands
import time
from dotenv import load_dotenv
import distance
from os import getenv, remove
from functools import lru_cache
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


load_dotenv('dev.env')

JACCARD_SIMILARITY_THRESHOLD = getenv("CUSTOM_PLAYER_NAME_JACCARD_THRESHOLD", 0.9) # maybe tweak this with more knowledge

default_timeout = 60

intents = discord.Intents(messages=True, message_content=True, guilds=True)

url = getenv("API_URL")
headers = {
    'accept': 'application/json',
    'Content-Type': 'application/json',
}

def number_to_string(n):
    number_dict = {
        2: 'double',
        3: 'triple',
        4: 'quadruple',
        5: 'quintuple',
        6: 'six-times (wtf?)',
        7: 'seven-times'
        # Add more if needed
    }
    return number_dict.get(n, '')

@lru_cache(maxsize=128)
def get_potential_players():
    """
    Get all potential players from the API
    :return: player_object list
    """
    response = requests.get(url + "/players", headers=headers)
    return json.loads(response.text)["results"]

class Game():
        """
        A class to represent a game.

        Attributes
        ----------
        game_id : str
            a unique identifier for the game
        player_list : list
            a list of players participating in the game

        Methods
        -------
        __init__(self, player_list, game_id):
            Constructs all the necessary attributes for the game object.
        """
        def __init__(self, player_list=None, game_id = None):
            """
            Constructs all the necessary attributes for the game object.

            Parameters
            ----------
                player_list : list
                    a list of players participating in the game
                game_id : str
                    a unique identifier for the game
            """
            if player_list is None:
                player_list = list()
            self.game_id = game_id
            self.game_timeout = time.time() + default_timeout
            self.player_list = player_list
            self.game_name = None


class Player():
    """
    A class to represent a player.
    """
    def __init__(self,player_name = None, player_id = None):
        """
        Constructs all the necessary attributes for the player object.
        :param player_id:
        :param player_name:
        """
        if player_id is None and player_name is not None:
            player_id = self.get_player_id_for_name(player_name)
        elif player_id is not None and player_name is None:
            player_name = self.get_player_name_for_id(player_id)
        else:
            raise Exception("Either player_name or player_id must be provided")
        self.player_id = player_id
        self.player_name = player_name
        self.points = 0

    @staticmethod
    def get_player_id_for_name(player_name,only_in_game: Game = None):
        if only_in_game is not None:
            potential_players =  only_in_game.player_list
            potential_players = [{"name": player.player_name, "player_id": player.player_id} for player in potential_players]
        else:
            potential_players = get_potential_players()

        for player_obj in potential_players:
            similarity = 1 - distance.jaccard(player_name.lower(), player_obj["name"].lower())
            if similarity > float(JACCARD_SIMILARITY_THRESHOLD):
                return player_obj["player_id"]

        raise Exception("Player not found")



    @staticmethod
    def get_player_name_for_id(player_id):
        potential_players = get_potential_players()
        for player_obj in potential_players:
            if player_obj["player_id"] == player_id:
                return player_obj["name"]
# client secret
# Qa6hSqdaKMHwcoyZm8pdOAe0E8qJ9z2M # todo remove

# db user doko pw uawohgdawiondiawud
#root pw uawohgdawiondiawuduawohgdawiondiawud



class DoppelkopfBot(commands.Bot):
    """
    A class to represent the discord bot.

    Attributes
    ----------
    game : Game
        the current game object
    in_game : bool
        a flag to toggle if a game is currently running
    debug_mode : bool
        a flag to toggle debug mode
    channel_ID : str
        the channel ID for the discord bot
    """
    def __init__(self, *args, **kwargs):
        """
        Constructs all the necessary attributes for the discord bot object.
        """
        self.game = None
        self.in_game = False
        self.debug_mode = False
        self.channel_ID = int(getenv("DISCORD_BOT_CHANNEL_ID"))
        # todo game name?
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        """
        A method to print the bot user when the bot is ready.
        """
        print('We have logged in as {0.user}'.format(bot))
        await bot.change_presence(activity=discord.Game(name="Doppelkopf"))
        await bot.get_channel(self.channel_ID).send("Bot is ready")

    # --------- start command methods ------------
    async def start_game(self, message):
        """
        A method to start a game with 4 players.
        :param message:
        """
        if self.in_game:
            await message.channel.send("Game already running")
            return

        game = Game()

        for player_name in message.content.split()[1].split(","):
            try:
                player = Player(player_name)
            except Exception as e:
                if self.debug_mode:
                    await message.channel.send(e)
                if "Player not found" in str(e):
                    await message.channel.send(f"Error adding player: {player_name} does not exist")
                else:
                    await message.channel.send(f"Error adding player: {player_name}")
                return
            if self.debug_mode:
                await message.channel.send(f"Found player {player.player_name} with id {player.player_id}.")
            game.player_list.append(player)

        if len(game.player_list) != 4:  # todo, support n players with only 4 per round
            await message.channel.send("Wrong number of players")
            return
        # match all but the first two words
        game_name = message.content.split()[2:]
        game_name = " ".join(game_name)
        payload = {
            "game_name": game_name,
            "is_closed": False,
            "players": [player.player_id for player in game.player_list]
        }
        try:  # make game
            res = requests.post(url + "/games/", headers=headers, data=json.dumps(payload))
            game_obj = json.loads(res.text)
            game.game_id = game_obj["game_id"]
            self.in_game = True
            self.game = game
            self.game.game_name =  game_name
            await message.channel.send('Game started')
            return
        except:
            self.in_game = False
            self.game = None
            await message.channel.send("Error starting game")
            return

    async def stop_game(self, message):
        """
        A method to stop the current game.
        :param message:
        """
        if self.in_game:
            self.in_game = False
            res = requests.post(url + "/games/" + str(self.game.game_id) + "/commit_game/", headers=headers)
            if res.status_code == 201:
                await message.channel.send('Game stopped')
            else:
                await message.channel.send('Error stopping game')
            await message.channel.send('Stopping game')
            await self.make_round_plot(self.game.game_id, message) # make a plot of the current (soon ended) game
            self.game = None
            return
        else:
            await message.channel.send('No game running')
            return

    async def get_players_with_pflichtsolo_ahead(self, message):
        """
        A method to get the players with Pflichtsolo ahead.
        :param message:
        """
        res = requests.get(url + "/games/" + str(self.game.game_id) + "/get_pflichtsolo/", headers=headers)
        players = json.loads(res.text)
        player_list = []
        for player in players:
            player_list.append(player["name"])
        player_string = ", ".join(player_list)
        await message.channel.send(f"Players with Pflichtsolo ahead: {player_string}")
        return

    async def get_points(self, message):
        """
        A method to get the player points for the current game in a nice format.
        :param message:
        """
        res = requests.get(url + "/games/" + str(self.game.game_id) + "/rounds/", headers=headers)  #
        rounds = json.loads(res.text)
        # exapmple rounds [{"game":18,"points":0,"created_at":"2024-05-23T17:58:11.876660Z","player_points":[{"player":{"player_id":"6b524db1-2e1b-43d5-ba85-82bd20b6f31a","name":"Valentin"},"points":100,"game_id":null,"round_id":9},{"player":{"player_id":"6664b7ec-e639-498c-92ef-0ee32481eef9","name":"Raven"},"points":-100,"game_id":null,"round_id":9},{"player":{"player_id":"28bd3a2f-bd53-4832-9854-fafb69da6a31","name":"caspar"},"points":-100,"game_id":null,"round_id":9},{"player":{"player_id":"32a56e51-46f1-4c7b-87e6-c15a055473c9","name":"Till"},"points":-100,"game_id":null,"round_id":9}]}]
        # calc points for each player
        player_points = {}
        for round in rounds:
            for player_point in round["player_points"]:
                if player_point["player"] not in player_points:
                    player_points[player_point["player"]] = 0
                player_points[player_point["player"]] += player_point["points"]
        # translate player ids to names
        #player_points = {Player.get_player_name_for_id(player_id): points for player_id, points in player_points.items()}
        player_points_string_fancy = ""
        for player_id in player_points:
            player_points_string_fancy += f"{Player.get_player_name_for_id(player_id)}: {player_points[player_id]}\n"
        #player_points_string_fancy = [f"{Player.get_player_name_for_id(player)}: {player_points['player']}" for player in player_points]
        round_string = f'Points after round {len(rounds)}:'
        send_string = "``"+round_string + "\n" + (player_points_string_fancy)+"``"
        await message.channel.send(send_string)
        if len(message.content.split()) > 1 and message.content.split()[1] == "-v":
            await self.make_round_plot(self.game.game_id, message)
        return

    async def get_bock_status(self, message):
        """
        A method to get the bock status of the current game.
        :param message:
        """
        res = requests.get(url + "/games/" + str(self.game.game_id) + "/get_bock_status/", headers=headers)
        bock_status = json.loads(res.text)
        bock_status_list = bock_status["bock_round_status"]
        amount = len(bock_status_list)
        if amount == 0:
            await message.channel.send("No bockrounds")
            return
        to_send = """``Bockrounds:\n"""

        bock_status_list.sort()
        last_remaining_round = 0
        for remaining_rounds in bock_status_list:
            if last_remaining_round != remaining_rounds:
                if remaining_rounds -last_remaining_round == 1:
                    to_send += f"bockround for {remaining_rounds -last_remaining_round} round\n"
                else:
                    to_send += f"{number_to_string(amount)} bockround for {remaining_rounds -last_remaining_round} rounds\n"
                last_remaining_round = remaining_rounds
            amount -= 1
        to_send += "``"
        await message.channel.send(to_send)
        return

    async def add_round(self, message):
        """
        A method to add points for a normal two player team game.
        :param message: should be in the format <player1>,<player2> points caused_bock_parallel
        """
        game_command_list = message.content.split(" ")  # interpret the text as a points command to add a round

        if len(game_command_list) < 2 or len(game_command_list) > 3:
            await message.channel.send('Error while parsing as points command')
            return
        try:
            if "," not in game_command_list[0]:  # solo. format solo Player_name points (not points*3)
                points_winner = int(game_command_list[1])
                winners = [game_command_list[0], ]
            else:  # team game normal
                winners = game_command_list[0].split(",")  # format player1,player2 points
                points_winner = int(game_command_list[1])

            winner_ids = [Player.get_player_id_for_name(player, only_in_game=self.game) for player in winners]
            if len(game_command_list) == 3:
                bock_parallel = int(game_command_list[2])
            else:
                bock_parallel = 0
            payload = {
                "points": points_winner,
                "winning_players": winner_ids,
                "losing_players": [player.player_id for player in self.game.player_list if
                                   player.player_id not in winner_ids],
                "caused_bock_parrallel": bock_parallel
            }
            if self.debug_mode:
                await message.channel.send(json.dumps(payload, indent=4))
            res = requests.post(url + "/games/" + str(self.game.game_id) + "/add_round/", headers=headers,
                                data=json.dumps(payload))
            succ = res.status_code == 201
            if not succ:
                await message.channel.send("Error adding round")
                return
            await message.channel.send('Round added')
        except:
            await message.channel.send('Error adding round')
            return

    async def get_games(self, message):
        """
        A method to get the last 5 games.
        :param message:
        """

        page_number = 1
        response = requests.get(f"{url}/games?page={page_number}", headers=headers)
        message_to_send = """```"""
        games = json.loads(response.text)
        for game in games["results"][:5]:
            date = datetime.datetime.strptime(game["created_at"], "%Y-%m-%dT%H:%M:%S.%f%z")
            fancy_date = date.strftime("%d.%m.%Y %H:%M")
            fancy_result_string = '\n'.join([f"{Player.get_player_name_for_id(player['player'])}: {player['points']}" for player in game["player_points"]])
            game_name = game["game_name"]
            message_to_send += f"Game {game_name} from {fancy_date} with results {fancy_result_string}\n"
            #(f"Game {game_name} from {fancy_date} with results {fancy_result_string}")
        message_to_send += "```"
        await message.channel.send(message_to_send)
        return

    async def undo_round(self, message):
        """
        A method to undo the last round.
        :param message:
        """
        res = requests.post(url + "/games/" + str(self.game.game_id) + "/undo_round/", headers=headers)
        if res.status_code == 200:
            await message.channel.send('Round undone')
        else:
            await message.channel.send('Error undoing round')
        return

    async def get_players(self, message):
        """
        A method to get all players.
        :param message:
        """
        if message.content.startswith('!get_players'):
            res = requests.get(url + "/players", headers=headers)
            players = json.loads(res.text)
            player_list = []
            for player in players["results"]:
                player_list.append(player["name"])
            player_string = ", ".join(player_list)
            await message.channel.send(f"Players: {player_string}")
            return

    async def create_player(self, message):
        """
        A method to create a player.
        :param message:
        """
        player_name = message.content.split()[1]
        res = requests.get(url + "/players", headers=headers)
        players = json.loads(res.text)
        for player in players["results"]:
            if player["name"] == player_name:
                await message.channel.send(f"Player {player_name} already exists")
                return
        payload = {
            "name": player_name
        }
        res = requests.post(url + "/players/", headers=headers, data=json.dumps(payload))
        if res.status_code == 201:
            await message.channel.send(f"Player {player_name} created")
        else:
            await message.channel.send("Error creating player")
        return

    async def debug_mode(self, message):
        """
        A method to toggle debug mode.
        :param message:
        """
        self.debug_mode = not self.debug_mode
        await message.channel.send('Debug mode: ' + str(self.debug_mode))
        if self.debug_mode:
            try:
                await message.channel.send('Players: ' + str([player.player_name for player in self.game.player_list]))
                await message.channel.send('Game ID: ' + str(self.game.game_id))
                await message.channel.send('Player IDs: ' + str([player.player_id for player in self.game.player_list]))
            except:
                await message.channel.send(
                    'Lol crashed while writing debug report, likely uncatched Null pointer I am too lazy to fix. But thats no problem, I can recover.')
        return

    async def reload_game(self, message):
        """
        A method to reload a game. via game_id
        :param message:
        """
        game_id = message.content.split()[1]
        payload = {
            "game_id": game_id
        }
        res = requests.get(url + "/games/" + str(game_id), headers=headers, data=json.dumps(payload))
        game_obj = json.loads(res.text)
        game = Game()
        game.game_id = game_obj["game_id"]
        game.game_name = game_obj["game_name"]
        game.player_list = [Player(player_id = player_id) for player_id in game_obj["players"]]
        self.game = game
        self.in_game = True
        await message.channel.send('Game reloaded')
        return

    async def make_round_plot(self, game_id, message):
        """
        A method to make a plot at the end of a game.
        :param game_id:
        :return:
        """


        payload = {
            "game_id": game_id
        }
        df_all = pd.DataFrame()
        for player_id in [player.player_id for player in self.game.player_list]:
            res = requests.get(url + "/stats/" + str(player_id) + "/round_points/", headers=headers,
                               data=json.dumps(payload))

            player_points = json.loads(res.text)
            player_name = Player.get_player_name_for_id(player_id)
            df_zero = pd.DataFrame({'player': [player_name], 'points': [0]})
            df = pd.DataFrame(player_points)
            df = pd.concat([df_zero, df])

            df["player"] = player_name
            df["points_cusum"] = df['points'].cumsum()
            df["discret_axis"] = range(0, len(df))
            df_all = pd.concat([df_all, df])

        sns.set_theme(style="darkgrid")
        plt.figure(figsize=(10, 6))

        sns.lineplot(data=df_all, x='discret_axis', y='points_cusum',hue='player')
        plt.xlabel("Rounds")

        plt.ylabel('Points')
        plt.title(f'Points for Game {self.game.game_name}')
        # rotate x axis
        plt.xticks(rotation=45)
        # more space for x axis
        plt.tight_layout()
        plt.savefig(fname='plot')
        await message.channel.send(file=discord.File('plot.png'))
        plt.clf()
        remove('plot.png')

    async def help_message(self, message):
        """
        A method to show a help message.
        :param message:
        """
        message_to_send = "Commands:\n"
        for command in self.commands:
            message_to_send += f"{command}:\n {self.commands[command]['description']}\n{self.commands[command]['usage']}\n\n"
        # send in discord code block
        await message.channel.send(f"```{message_to_send}```")
    commands = {
        "start": {
            "description": "start a game with 4 players",
            "usage": "!start player1,player2,player3,player4 game_name",
            "method": start_game,
            "command_prefix": "!start",         #todo start 1h timer for game?
            "only_in_game": False
           },
        "reload": {
            "description": "reload a game",
            "usage": "!reload game_id",
            "method": reload_game,
            "command_prefix": "!reload",
            "only_in_game": False
           },
        "stop": {
            "description": "stop the current game",
            "usage": "!stop",
            "method": stop_game,
            "command_prefix": "!stop",
            "only_in_game": True
           },
        "get_pflichtsolo_ahead": {
            "description": "show players with Pflichtsolo ahead",
            "usage": "!pflichtsolo",
            "method": get_players_with_pflichtsolo_ahead,
            "command_prefix": "!pflichtsolo",
            "only_in_game": True
           },
        "points": {
            "description": "show points of all current players for the current game",
            "usage": "!points",
            "method": get_points,
            "command_prefix": "!points",
            "only_in_game": True
           },
        "bock_status": {
            "description": "show the bock status of the current game",
            "usage": "!bock",
            "method": get_bock_status,
            "command_prefix": "!bock",
            "only_in_game": True
              },
        "normal": {
            "description": "add points for winning team",
            "usage": "<player1>,<player2> points amount_caused_bock_parallel",
            "method": add_round,
            "command_prefix": None,
            "only_in_game": True
           },
        "solo": {
            "description": "add points for solo winner",
            "usage": "<player> points(not points*3) amount_caused_bock_parallel",
            "method": add_round,
            "command_prefix": None,
            "only_in_game": True
           },
        "undo_round": {
            "description": "undo the last round",
            "usage": "!undo_round",
            "method": undo_round,
            "command_prefix": "!undo_round",
            "only_in_game": True
              },
        "get_games": {
            "description": "get the last 5 games",
            "usage": "!get_games",
            "method": get_games,
            "command_prefix": "!get_games",
            "only_in_game": False
           },
        "get_players": {
            "description": "get all players",
            "usage": "!get_players",
            "method": get_players,
            "command_prefix": "!get_players",
            "only_in_game": False
           },
        "create_player": {
            "description": "create a player",
            "usage": "!create_player <player_name>",
            "method": create_player,
            "command_prefix": "!create_player",
            "only_in_game": False
           },
        "debug": {
            "description": "toggle debug mode and send debug report",
            "usage": "!debug",
            "method": debug_mode,
            "command_prefix": "!debug",
            "only_in_game": False
           },
        "help": {
            "description": "show this help message",
            "usage": "!help",
            "method": help_message,
            "command_prefix": "!help",
            "only_in_game": False
           }
    }

    async def on_message(self, message):
        """
        A method to handle messages sent to the bot.
        :param message:
        :return:
        """
        if message.author == bot.user: # no self response
            return
        if message.channel.id != self.channel_ID:  # bot channel
            return

        if message.content.startswith('!'):
            try:
                for command in [command_loop for command_loop in self.commands if self.commands[command_loop]["command_prefix"] is not None]:
                    if message.content.startswith(self.commands[command]["command_prefix"]):
                        if self.commands[command]["only_in_game"] and not self.in_game:
                            await message.channel.send("No game running")
                            return
                        await self.commands[command]["method"](self, message)
                        return
            except Exception as e:
                await message.channel.send('Command failed')
                if self.debug_mode:
                    await message.channel.send(e)
                return
            await message.channel.send('Unknown Command')
            return
        elif self.in_game:
            try:
                await self.add_round(message)
            except Exception as e:
                await message.channel.send("Error adding round")
                if self.debug_mode:
                    await message.channel.send(e)


bot = DoppelkopfBot(command_prefix='!', intents=intents)
bot.run(getenv("DISCORD_TOKEN"))
