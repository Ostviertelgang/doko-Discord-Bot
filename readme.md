# doko Discord Bot
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
WIP: for now ``!`` is the command prefix, try !help, start a game with !start player1 player2 player3 player4, then add points with ``winner1,winner2 points`` or for a solo ``winner1 points``.


## Planned Features
2. Full integration of the doko_api statistics endpoint
2. Matplotlib integration for visualizing the scores

## todos after 1st playtest
2. round undo
4. discuss if bockrunde is part of frontend or backend, and implement it accordingly
5. adding player who do not exist does not get right anwers 
6. cleanup after game end failure (e.g. player not found) seems to have some bugs and youj cannot start a new game later
7. who played a solo already?