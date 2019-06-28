import discord
import redis
import os
import asyncio

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

def change_prefix():
  global prefixchar
  if redis_server.exists('current.prefix'):
    #using previously set prefix
    prefixchar = redis_server.get('current.prefix').decode('utf-8')
  else: 
    redis_server.set('current.prefix', '.')
    prefixchar = redis_server.get('current.prefix').decode('utf-8')

change_prefix()

@client.event
async def on_ready():
  print('Logged in as {0.user}, with prefix {1}'.format(client,prefixchar))

@client.event
async def on_message(message):
  if message.author == client.user:
    return

  #Get prefix not knowing current one.
  if message.content == '.getprefix':
    await message.channel.send(embed=discord.Embed(title=str(message.author), description="Current prefix is {0}".format(redis_server.get('current.prefix').decode('utf-8'))))

  #check for prefix first
  if message.content.startswith(prefixchar):
    uinput = str(message.content).split(" ", 1)

    command = uinput[0].strip(prefixchar)

    #try to isolate params, may be NULL
    try:
      params = uinput[1]
    except IndexError:
      params = ""

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

    #Owner only
    if author_id in os.getenv('owner_id'):
      if command == 'flushdb':
        await channel.send(embed=discord.Embed(title="Are you sure? This will delete everything in the DB (Y/n)", color=16724787))
        
        def check(message):
            if str(message.author.id) in os.getenv('owner_id') and str(message.content).lower() == 'n' and message.channel == channel:
              raise asyncio.TimeoutError
            return str(message.author.id) in os.getenv('owner_id') and str(message.content).lower() == 'y' and message.channel == channel
        try:
          msg = await client.wait_for('message', timeout=15.0, check=check)
        except asyncio.TimeoutError:
          await channel.send(embed=discord.Embed(title="FlushDB canceled."))
        else:
          redis_server.flushdb()
          await channel.send(embed=discord.Embed(title="Current database flushed, prefix reset to '.'"))
          change_prefix()
       
      if command == 'changeprefix':
        redis_server.set('current.prefix', params)
        change_prefix()
        await channel.send(embed=discord.Embed(title=author_name, description='Prefix changed to {0}'.format(params)))

    #Currency command
    if command in ['$', 'cur', 'currency']:

      #No parameters, use author.ID to search  
      if params == "":
        #check if ID exists
        if redis_server.exists('id.'+author_id):
          #search using it
          await channel.send(embed=discord.Embed(title='', description= '**'+author_name+'**'+ ' has {0}'.format(redis_server.get('id.'+author_id).decode('utf-8')), color=39270))
        #ID doesn't exist
        else:
          #Sets the author's amount to zero
          redis_server.set('id.'+author_id, '0'.encode('utf-8'))
          #Creates a hash table with Username -> user_discrim -> user_ID, for username searching
          redis_server.hset('name.'+author_uname_only, author_discrim, author_id.encode('utf-8'))
          #ID exists now, safe to get
          await channel.send(embed=discord.Embed(title='', description='**'+author_name+'**'+' has {0}'.format(redis_server.get('id.'+author_id).decode('utf-8')), color=39270))
      
      #Search using ID
      elif redis_server.exists('id.'+params):
        await channel.send(embed=discord.Embed(title='', description='**'+str(client.get_user(int(params)))+'**'+' has {0}'.format(redis_server.get('id.'+params).decode('utf-8')), color=39270))
      
      #Check using username
      else:
        if '#' in params:
          split_params = params.split('#', 1)
          #hget, because it'll return nil if empty anyways
          user_prob_id = redis_server.hget('name.'+str(split_params[0]), split_params[1])
          #Search came back with results
          if user_prob_id != None:
            user_id = str(user_prob_id.decode('utf-8'))
            await channel.send(embed=discord.Embed(title='', description='**'+str(client.get_user(int(user_prob_id)))+'**'+' has {0}'.format(redis_server.get('id.'+user_id).decode('utf-8')), color=39270))
          #Fail on attempts
          else:
            await channel.send(embed=discord.Embed(title=author_name, description='{0} not found.'.format(str(params)), color=16724787))

        #Attempts to check using username
        else:
          
          try:
            user_prob_id = str(redis_server.hvals('name.'+params)[0].decode('utf-8'))
          except IndexError:
            user_prob_id = ''
          if user_prob_id != '':
            print(user_prob_id)
            #get, since we know it exists because names were saved in init of user into cur db.
            await channel.send(embed=discord.Embed(title='', description='**'+str(client.get_user(int(user_prob_id)))+'**'+' has {0}'.format(redis_server.get('id.'+user_prob_id).decode('utf-8')), color=39270))

          #Fail on attempts
          else:
            await channel.send(embed=discord.Embed(title=author_name, description='{0} not found.'.format(str(params)), color=16724787))

        
client.run(os.getenv('bot_token'))