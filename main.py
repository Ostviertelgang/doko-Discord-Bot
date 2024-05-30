import datetime

import discord
import requests
import json
from discord.ext import commands
import time
#from dotenv import load_dotenv
import distance
from os import getenv
from functools import lru_cache

JACCARD_SIMILARITY_THRESHOLD = getenv("CUSTOM_PLAYER_NAME_JACCARD_THRESHOLD", 0.9) # maybe tweak this with more knowledge

default_timeout = 60

intents = discord.Intents(messages=True, message_content=True, guilds=True)

url = getenv("API_URL")
headers = {
    'accept': 'application/json',
    'Content-Type': 'application/json',
}
# intents = intents.messages = True # might be required by discord


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
        def __init__(self, player_list = list(), game_id = None):
            """
            Constructs all the necessary attributes for the game object.

            Parameters
            ----------
                player_list : list
                    a list of players participating in the game
                game_id : str
                    a unique identifier for the game
            """
            self.game_id = game_id
            self.game_timeout = time.time() + default_timeout
            self.player_list = player_list


class Player():
    """
    A class to represent a player.
    """
    def __init__(self,player_name, player_id = None):
        """
        Constructs all the necessary attributes for the player object.
        :param player_id:
        :param player_name:
        """
        if player_id is None and player_name is not None:
            player_id = self.get_player_id_for_name(player_name)
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
        try:
            for player_obj in potential_players:
                similarity = 1 - distance.jaccard(player_name, player_obj["name"])
                if similarity > float(JACCARD_SIMILARITY_THRESHOLD):
                    return player_obj["player_id"]

        except Exception as e:
            print("Error while getting player id for name")
            print(e)


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
        # todo, add a commands dict to clean up the on_message method
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        """
        A method to print the bot user when the bot is ready.
        """
        print('We have logged in as {0.user}'.format(bot))
        await bot.change_presence(activity=discord.Game(name="Doppelkopf"))
        await bot.get_channel(self.channel_ID).send("Bot is ready")

    async def on_message(self, message):
        """
        A method to handle messages sent to the bot. (ugly and long :( )
        :param message:
        :return:
        """
        if message.author == bot.user: # no self response
            return
        if message.channel.id != self.channel_ID:  # bot channel
            return


        # todo use the task_spawner pattern to clean up the on_message method

        if message.content.startswith('!start'):
            if self.in_game:
                await message.channel.send("Game already running")
                return
            await message.channel.send('Starting game')
            game = Game()

            for player_name in message.content.split()[1:]:
                try:
                    player = Player(player_name)
                except: # todo special exception for player_id not found
                    # await message.channel.send("Player " + player_name + " does not exist")
                    await message.channel.send(f"Error adding player: {player_name} does not exist")
                    return
                if self.debug_mode:
                    await message.channel.send(f"Found player {player.player_name} with id {player.player_id}.")
                else:
                    await message.channel.send(f"Added player {player_name} to game")
                game.player_list.append(player)

            if len(game.player_list) != 4: # todo, support n players with only 4 per round
                await message.channel.send("Wrong number of players")
                return
            payload = {
                "game_name": "Discord Bot Game", # todo make editable?!
                "is_closed": False,
                "players": [player.player_id for player in game.player_list]
            }
            try: # make game
                res = requests.post(url + "/games/", headers=headers, data=json.dumps(payload))
                game_obj = json.loads(res.text)
                game.game_id = game_obj["game_id"]
                self.in_game = True
                self.game = game
                return
            except:
                self.in_game = False
                self.game = None
                await message.channel.send("Error starting game")
                return

        if message.content.startswith('!get_games'):
            params = {'ordering': '-created_at'} # todo check if this works and if it needs to get implementde in the server
            response = requests.get(url + "/games", headers=headers, params=params)
            games = json.loads(response.text)
            game_list = []
            for game in games["results"][-5:]:
                created_at = datetime.datetime.strptime(game["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
                fancy_date = created_at.strftime("%Y.%m.%d %H:%M")
                fancy_result_string = [f"{Player.get_player_name_for_id(player['player'])}: {player['points']}" for player in game["player_points"]]
                await message.channel.send(f"Game from {fancy_date} with results {fancy_result_string}")
            return

        if message.content.startswith('!get_players'):
            res = requests.get(url + "/players", headers=headers)
            players = json.loads(res.text)
            player_list = []
            for player in players["results"]:
                player_list.append(player["name"])
            player_string = ", ".join(player_list)
            await message.channel.send(f"Players: {player_string}")
            return

        if message.content.startswith('!create_player'):
            player_name = message.content.split()[1]
            payload = {
                "name": player_name
            }
            res = requests.post(url + "/players/", headers=headers, data=json.dumps(payload))
            if res.status_code == 201:
                await message.channel.send(f"Player {player_name} created")
            else:
                await message.channel.send("Error creating player")
            return


        if message.content.startswith('!stop'):
            if self.in_game:
                self.in_game = False
                res = requests.post(url + "/games/" + str(self.game.game_id) + "/commit_game/", headers=headers)
                if res.status_code == 201:
                    await message.channel.send('Game stopped')
                else:
                    await message.channel.send('Error stopping game')
                await message.channel.send('Stopping game')
                self.game = None
                return
            else:
                await message.channel.send('No game running')
                return

        if message.content.startswith('!help'):
            await message.channel.send('!start player1 player2 player3 player4 - start a game with 4 players\n'
                                       '!stop - stop the current game\n'
                                       'points - (only in game) show points of all players\n'
                                       '<player1>,<player2> points - (only in game) add points for winning team\n'
                                       '!<player> points - (only in game) add points for solo winner\n'
                                       '!debug - toggle debug mode\n'
                                       '!help - show this help message')
            return

        if message.content.startswith('!debug'):
            self.debug_mode = not self.debug_mode
            await message.channel.send('Debug mode: ' + str(self.debug_mode))
            if self.debug_mode:
                try:
                    await message.channel.send('Players: ' + str([player.player_name for player in self.game.player_list]))
                    await message.channel.send('Game ID: ' + str(self.game.game_id))
                    await message.channel.send('Player IDs: ' + str([player.player_id for player in self.game.player_list]))
                except:
                    await message.channel.send('Lol crashed while writing debug report, likely uncatched Null pointer I am too lazy to fix. But thats no problem, I can recover.')
            return

        if message.content.startswith('!'):  # unhandled command
            await message.channel.send('Unknown Command')
            return

        if not self.in_game:
            return

        ## -------- only in game commands ------
        #todo start 1h timer for game?

        if message.content.startswith('points'): # todo make this use the command syntax to work cleanly with a player called "points"
            """
            get the player points for the current game in a nice format
            """
            res = requests.get(url + "/games/" + str(self.game.game_id) + "/rounds/", headers=headers)#
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
            player_points = {Player.get_player_name_for_id(player_id): points for player_id, points in player_points.items()}
            await message.channel.send(json.dumps(player_points, indent=4)) # todo make fancy
            return


        game_command_list = message.content.split(" ") # interpret the text as a points command to add a round

        if len(game_command_list) < 2 or len(game_command_list) > 2:
            await message.channel.send('Error while parsing as points command')
            return
        try:
            if "," not in game_command_list[0]:  # solo. format solo Player_name points (not points*3)
                points_winner = int(game_command_list[1])
                winners = [game_command_list[0],]
            else:  # team game normal
                winners = game_command_list[0].split(",") # format player1,player2 points
                points_winner = int(game_command_list[1])

            winner_ids = [Player.get_player_id_for_name(player,only_in_game=self.game) for player in winners]
            payload = {
                "points": points_winner,
                "winning_players": winner_ids,
                "losing_players": [player.player_id for player in self.game.player_list if player.player_id not in winner_ids]
            }
            if self.debug_mode:
                await message.channel.send(json.dumps(payload, indent=4))
            res = requests.post(url + "/games/" + str(self.game.game_id) + "/add_round/", headers=headers, data=json.dumps(payload))
            succ = res.status_code == 201
            if not succ:
                await message.channel.send("Error adding round")
                return
            await message.channel.send('Round added')
        except:
            await message.channel.send('Error adding round')
            return


bot = DoppelkopfBot(command_prefix='!', intents=intents)
bot.run(getenv("DISCORD_TOKEN"))
