# doko-Discord-Bot

![Banner picture](https://i.imgur.com/5WsppRT.png)
This is a frontend for the doko-API Doppelkopf point counting suite in form of a Discord bot.

You can find the server part [here](https://github.com/Ostviertelgang/doko-API).

## Features
1. Do the basic point counting for a doppelkopf game, with bockrounds and pflichtsolo
2. Start games, keep track of the poins of each player over a series of rounds
3. Visualize player statics over a game or over all time
4. Implement the [doko-API](https://github.com/Ostviertelgang/doko-API) server to save the points long term


## Installation
1. Install the doko-API server from [here](https://github.com/Ostviertelgang/doko-API).
2. Get the Discord bot token from the discord developer portal. Here is a [guide](https://discordpy.readthedocs.io/en/stable/discord.html).
3. Make a bot channel in your discord server and get the channel id, to use it in the prod.env file.

### get the docker image from dockerhub:
Will come with release 1.0 of the bot and the API.

### to build the docker image yourself:
1. ``git clone https://github.com/Ostviertelgang/doko-Discord-Bot.git``
2. ``cd doko-Discord-Bot``
3. Then I prefer docker compose, either just use the docker-compose.yml in the repo file or customize it from here:
```bash
version: '3.8'

services:
  discord_bot:
    build: ./
    command: python main.py
    env_file:
      - ./prod.env

```
4. Fill in the values in the prod.env file.  
  (You can leave the jaccard threshold empty (defaults to 0.9). It's used for the player name matching.)
5. ``docker compose up -d``  
5. Enjoy!

## Usage
Use ``!help`` to get a list of all commands with a short description and usage information.
Some commands, such as the commands getting the points are only availabe in game. 

General Usage:  
``!command [arg1,arg_1] [arg2] ...``

the most important commands:
```
!start player1,player2,player3,player4 game_name
winning_player1,winning_player2 points <optional: amount_of_bockrounds_caused> # for a normal game
winning_player points <optional: amount_of_bockrounds_caused> # for a solo
!points (-v for a graphical representation)
!bock # to get the current bockroundstatus
!pflichtsolo # to see which player still have their pflichtsolo to go.
!stop # close and commit the current game, get a summary plot of the game
```
#### Typical commands of a game:
```
!start Bob,Alice,Eve,Mallory just_gaming_no_spying
Bob,Alice 2 # Bob and Alice won and get 2 points, Eve and Mallory loose 2 points
Mallory,Eve 4 # Mallory and Eve won and get 4 points, Bob and Alice loose 4 points
Eve 2 # Eve played a solo, she gets 6 points, the others loose 2 points
!points # get the current points
Bob,Eve 12 1 # Bob and Eve won and caused a bockround
!bock # get the current bock status
!pflichtsolo # see who still has to play a solo
Bob,Alice 3 # Bob and Alice won and get 6 points (because of bockrunde), Eve and Mallory loose 6 points
!stop # close the game
```