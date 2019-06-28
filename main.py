import discord
import redis
import os

from dotenv import load_dotenv
load_dotenv()

debug = True
owner = os.getenv('owner_id')

redis_server = redis.Redis(
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

  #check for prefix first
  if message.content.startswith(str(prefixchar)):
    uinput = str(message.content).split(" ", 1)

    command = uinput[0].strip(prefixchar)

    #try to isolate params, may be NULL
    try:
      params = uinput[1]
    except IndexError:
      params = [""]

    channel = message.channel

    #Author details
    author_name = str(message.author)

    #using this method to ensure no discrim
    author_uname_only = author_name.split("#", 1)[0]
    author_discrim = str(message.author.discriminator)
    author_id = str(message.author.id)

    #Test commands, test response
    if debug:
      if command == 'teststore':
        split_params = params.split(" ", 1)
        if len(split_params) >= 2:
          redis_server.set(split_params[0], split_params[1].encode('utf-8'))
          await channel.send(embed=discord.Embed(title="", description=redis_server.get(split_params[0]).decode('utf-8')))
        else:
          embed = discord.Embed(title=author_name + ' Invalid Command', description='Command requires 2 parameters {0} given'.format(len(split_params)))
          await channel.send(embed=embed)

    if command in ['$', 'cur', 'currency']:
      if '#' in params:
        split_params = params.split('#', 1)

      #No parameters, use ID to search  
      if params == "":
        #check if ID exists
        if redis_server.exists('id_'+author_id) == 1:
          #search using it
          await channel.send(discord.Embed(title=author_name, description=' has {0}'.format(redis_server.get('id'+author_id).decode('utf-8'))))
        #ID doesn't exist
        else:
          #Sets the author's amount to zero
          redis_server.set('id_'+author_id, '0'.encode('utf-8'))
          #Creates a hash table with Username -> user_discrim -> user_ID, for username searching
          redis_server.hset('name_'+author_uname_only, author_discrim, author_id.encode('utf-8'))
          #ID exists now, safe to get
          await channel.send(discord.Embed(title=author_name, description=' has {0}'.format(redis_server.get('id_'+author_id).decode('utf-8'))))

      #Attempts to check using username
      user_prob_id = redis_server.hvals(params)[0]
      if user_prob_id != '':
        #search if exists using user_prob_id
        if redis_server.exists(user_prob_id) == 1:
          #finally search
          await channel.send(discord.Embed(title=client.user.get, description=' has {0}'.format(redis_server.get(author_id).decode('utf-8'))))

      else:
        await channel.send(discord.Embed(title = author_name))
client.run(os.getenv('bot_token'))