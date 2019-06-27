import discord
import redis

from dotenv import load_dotenv
load_dotenv()

import os

client = discord.Client()

prefixchar = "."

@client.event
async def on_ready():
    print('Logged in as {0.user}, with prefix {1}'.format(client,prefixchar))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith(str(prefixchar)):
        uinput = str(message.content).split(" ")
        command = uinput.pop(0)
        

client.run(os.getenv('bot_token'))