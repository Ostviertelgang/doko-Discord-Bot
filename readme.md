# doko Discord Bot
This is a frontend for the doko_api Doppelkopf point counting solution in form of a Discord bot.

You can find the server part [here]() (soon).

## Features
1. Start games with existing players and keep track of the poins of each player over a series of rounds.
2. Get the current all time scores of a player.
## Installation

1. Install the api server from [here]() (soon).
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
4. Fill in the values in the prod.env file
5. ``docker compose up -d``  
5. Enjoy
## Planned Features
1. Add players
2. Full integration of the doko_api statistics endpoint
2. Matplotlib integration for visualizing the scores
3. 