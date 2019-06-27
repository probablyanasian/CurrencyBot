import discord
import redis
import os

from dotenv import load_dotenv
load_dotenv()

redisserver = redis.Redis(
  host=os.getenv('redis_hostname'),
  port=int(os.getenv('redis_port')), 
  password=(os.getenv('redis_password'))
)

client = discord.Client()

prefixchar = "."

@client.event
async def on_ready():
  print('Logged in as {0.user}, with prefix {1}'.format(client,prefixchar))

@client.event
async def on_message(message):
  if message.author == client.user:
    return

  #check for prefix helps slightly with efficiency (I think)
  #Yes, ik I should've chosen a faster lang if I wanted efficiency.

  if message.content.startswith(str(prefixchar)):
    uinput = str(message.content).split(" ")

    channel = message.channel
    if uinput[0] == str(prefixchar+'teststore'):
      if len(uinput) >= 3:
        redisserver.set(uinput[1], uinput[2].encode('utf-8'))
        await channel.send(redisserver.get(uinput[1]).decode('utf-8'))
  

client.run(os.getenv('bot_token'))