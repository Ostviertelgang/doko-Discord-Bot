# doko Discord Bot

![Banner picture](https://i.imgur.com/5WsppRT.png)
This is a frontend for the doko_api Doppelkopf point counting solution in form of a Discord bot.

You can find the server part [here](https://github.com/Ostviertelgang/doko-API).

## Features
1. Start games with existing players and keep track of the poins of each player over a series of rounds.
2. Get the current all time scores of a player.
3. Various getters and setters
## Installation

1. Install the api server from [here](https://github.com/Ostviertelgang/doko-API).
2. get the discord bot token from the discord developer portal.
3. make a bot channel in your discord server and get the channel id.

### to build the docker image yourself:
1. ``git clone https://github.com/Ostviertelgang/doko-Discord-Bot.git``
2. ``cd doko-Discord-Bot``
3. Then i prefer docker compose, either just use the docker-compose.yml file or customize it frome here:
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
  (You can leave the jaccard threshold empty (defaults to 0.9). Its used for the player name matching.)
5. ``docker compose up -d``  
5. Enjoy

## Usage
Use ``!help`` to get a list of all commands.
Some commands, such as the commands getting the points are only availabe in game. 

General Usage:  
``!command [arg1,arg_1] [arg2] ...``

the most important commands:
```
!start player1,player2,player3,player4 game_name
winning_player1,winning_player2 points <optional: amount_of_bockrounds_caused> # for a normal game
winning_player points <optional: amount_of_bockrounds_caused> # for a solo
!points
!bock # to get the current bockroundstatus
!pflichtsolo # to see which player still have their pflichtsolo to go.
!stop # close and commit the current game
```
#### Typical commands of a game:
```
!start Bob,Alice,Eve,Mallory just_gaming_no_spying
Bob,Alice 2 # Bob and Alice won
Mallory,Eve 4
Eve 2 # Eve played a solo
!points # get the current points
Bob,Eve 12 1 # Bob and Eve won and caused a bockround
!bock # get the current bock status
!pflichtsolo # see who still has to play a solo
Bob,Alice 3
!stop # close the game
```