import discord
import os

client = discord.Client()

prefixchar = "."

@client.event
async def on_ready():
    print('Logged in as {0.user}, with prefix %s'.format(client,prefixchar))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith(str(prefixchar+"hello")):
        await message.channel.send('Hello!')

client.run('your token here')