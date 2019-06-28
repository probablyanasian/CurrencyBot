import discord
import redis
import os
import asyncio
import time
import secrets

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

#Change the bot's prefix, currently only global prefix.
def change_prefix():
  global prefix_char
  if redis_server.exists('current.prefix'):
    #use newly/currently set currency
    prefix_char = redis_server.get('current.prefix').decode('utf-8')
  else: 
    redis_server.set('current.prefix', '.')
    prefix_char = redis_server.get('current.prefix').decode('utf-8')

#Change the currency name
def change_currency():
  global currency_type
  if redis_server.exists('current.currency'):
    #use newly/currently set currency 
    currency_type = redis_server.get('current.currency').decode('utf-8')
  else: 
    redis_server.set('current.currency', 'dollars')
    currency_type = redis_server.get('current.currency').decode('utf-8')

#sets db to default values
def default_all():
  change_prefix()
  change_currency()
  redis_server.set('last.drop', '0'.encode('utf-8'))

#Add to the currency database, and lookup database
def add_to_cur(author_id, author_uname, author_discrim):
  if redis_server.exists('id.'+author_id):
    return
  else:
    #Sets the author's amount to 100, to start off with
    redis_server.set('id.'+author_id, '100'.encode('utf-8'))
    #Creates a hash table with Username -> user_discrim -> user_ID, for username searching
    redis_server.hset('name.'+author_uname, author_discrim, author_id.encode('utf-8'))

#identifiable to user
def ident_to_id(ident):
  #Search using ID
  if redis_server.exists('id.'+ident):
    return(ident)
    
  #Attempts to check using username
  else:
    user_prob_id = redis_server.hvals('name.'+ident)
    if user_prob_id != []:
      user_id = str(user_prob_id[0].decode('utf-8'))
      #return id, since we know it exists because names were saved in init of user into cur db.
      return(user_id)

        #Fail on attempts
    else:
      if '#' in ident:
        split_params = ident.rsplit('#', 1)
        #hget, because it'll return nil if empty anyways
        user_prob_id = redis_server.hget('name.'+str(split_params[0]), split_params[1])
        #Search came back with results
        if user_prob_id != None:
          user_id = str(user_prob_id.decode('utf-8'))
          return(user_id)
        else:
          #Fail on attempts
          return(None)
  return(None)

default_all()

@client.event
async def on_ready():
  print('Logged in as {0.user}, with prefix {1}'.format(client,prefix_char))

@client.event
async def on_message(message):
  if message.author == client.user:
    return

  #Get prefix not knowing current one.
  if message.content == '.getprefix':
    await message.channel.send(embed=discord.Embed(title=str(message.author), description="Current prefix is {0}".format(redis_server.get('current.prefix').decode('utf-8'))))

  #check for prefix first
  if message.content.startswith(prefix_char):
    uinput = str(message.content).split(" ", 1)

    command = uinput[0].strip(prefix_char)

    #try to isolate params, may be NULL
    try:
      params = uinput[1]
    except IndexError:
      params = ""

    channel = message.channel

    #Author details
    #author name str(message.author)
    #uname only str(message.author).rsplit("#", 1)[0]
    #discriminator str(message.author.discriminator)
    #author id str(message.author.id)

    #Test commands, test response
    if debug:
      if command == 'teststore':
        split_params = params.split(" ", 1)
        if len(split_params) >= 2:
          redis_server.set(split_params[0], split_params[1].encode('utf-8'))
          await channel.send(embed=discord.Embed(title="", description=redis_server.get(split_params[0]).decode('utf-8')))
        else:
          embed = discord.Embed(title=str(message.author) + ' Invalid Command', description='Command requires 2 parameters {0} given'.format(len(split_params)))
          await channel.send(embed=embed)

    #Owner only
    if str(message.author.id) in os.getenv('owner_id'):
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
          default_all()
       
      if command == 'changeprefix':
        redis_server.set('current.prefix', params)
        change_prefix()
        await channel.send(embed=discord.Embed(title=str(message.author), description='Prefix changed to {0}'.format(params)))

      if command == 'changecurrency':
        redis_server.set('current.currency', params)
        change_currency()
        await channel.send(embed=discord.Embed(title=str(message.author), description='Currency changed to {0}'.format(params)))

      if command == 'award':
        split_params = params.split(' ', 1)
        try:
          add_value = int(split_params[0])
        except ValueError:
          await channel.send(embed=discord.Embed(title=str(message.author), description='Award amount is not a number.'))
          return
        try:
          supposed_id = ident_to_id(split_params[1])
        except IndexError:
          await channel.send(embed=discord.Embed(title=str(message.author), description='Requires 2 parameters'))
        if supposed_id != None:
          cur_bal = int(redis_server.get('id.'+supposed_id).decode('utf-8'))
          redis_server.set('id.'+supposed_id, str(cur_bal+add_value).encode('utf-8'))
          await channel.send(embed=discord.Embed(title=str(message.author), description=str(client.get_user(int(supposed_id)))+' recieved {0} {1}'.format(add_value, currency_type)))
        else: 
          await channel.send(embed=discord.Embed(title=str(message.author), description='Recipient is not in the DB'))

          
  
    #Currency command
    if command in ['$', 'cur', 'currency']:

      #No parameters, use author.ID to search  
      if params == "":
        #check if ID exists
        if redis_server.exists('id.'+str(message.author.id)):
          #search using it
          await channel.send(embed=discord.Embed(title='', description= '**'+str(message.author)+'**'+ ' has {0} {1}'.format(redis_server.get('id.'+str(message.author.id)).decode('utf-8'), currency_type), color=39270))
        #ID doesn't exist
        else:
          #Since ID doesn't exist yet, add it.
          add_to_cur(str(message.author.id), str(message.author).rsplit("#", 1)[0], str(message.author.discriminator))
          await channel.send(embed=discord.Embed(title='', description='**'+str(message.author)+'**'+' has {0} {1}'.format(redis_server.get('id.'+str(message.author.id)).decode('utf-8'), currency_type), color=39270))
      
      #Search using ID
      elif redis_server.exists('id.'+params):
        await channel.send(embed=discord.Embed(title='', description='**'+str(client.get_user(int(params)))+'**'+' has {0} {1}'.format(redis_server.get('id.'+params).decode('utf-8'), currency_type), color=39270))
        
      #Attempts to check using username
      else:
        user_prob_id = redis_server.hvals('name.'+params)
        if user_prob_id != []:
          user_id = str(user_prob_id[0].decode('utf-8'))
          #get, since we know it exists because names were saved in init of user into cur db.
          await channel.send(embed=discord.Embed(title='', description='**'+str(client.get_user(int(user_id)))+'**'+' has {0} {1}'.format(redis_server.get('id.'+user_id).decode('utf-8'), currency_type), color=39270))

            #Fail on attempts
        else:
          if '#' in params:
            split_params = params.split('#', 1)
            #hget, because it'll return nil if empty anyways
            user_prob_id = redis_server.hget('name.'+str(split_params[0]), split_params[1])
            #Search came back with results
            if user_prob_id != None:
              user_id = str(user_prob_id.decode('utf-8'))
              await channel.send(embed=discord.Embed(title='', description='**'+str(client.get_user(int(user_prob_id)))+'**'+' has {0} {1}'.format(redis_server.get('id.'+user_id).decode('utf-8'), currency_type), color=39270))
            else:
              #Fail on attempts
              await channel.send(embed=discord.Embed(title=str(message.author), description='{0} not found.'.format(str(params)), color=16724787))
          else:
            #Fail on attempts
            await channel.send(embed=discord.Embed(title=str(message.author), description='{0} not found.'.format(str(params)), color=16724787))

    if command == 'pick':
      #If not already in db, add them
      add_to_cur(str(message.author.id), str(message.author).rsplit("#", 1)[0], str(message.author.discriminator))
      #Temporary total var
      total_picked = 0
      #Loops through all the missed drops
      for message_id in redis_server.hkeys('drop.'+str(channel.id)):
        #Adds up the total
        total_picked += int(redis_server.hget('drop.'+str(channel.id), message_id))
        #Delete after "picked"
        redis_server.hdel('drop.'+str(channel.id), message_id)
      #Add to author's account
      cur_author_bal = int(redis_server.get('id.'+str(message.author.id)).decode('utf-8'))
      cur_author_bal += total_picked
      redis_server.set('id.'+str(message.author.id), str(cur_author_bal).encode('utf-8'))
      #Send message with who, and value picked up
      await message.channel.send(embed=discord.Embed(title='', description='**{0}** picked up {1} {2}'.format(str(message.author).rsplit("#", 1)[0], str(total_picked), currency_type)))

      #Need to check how to delete a message in discord.py 
      #await channel.delete_messages(int(redis_server.hkeys('drop.'+str(channel.id)))) TODO Fix if extra time
    
    #Store command
    if command in ['shop','store']:
      redis_server.hgetall('current.shop')
  
  #On a noncommand, every 3 minutes
  elif (round((time.time()), None) - int(redis_server.get('last.drop').decode('utf-8'))) > 180:
    #2 percent chance
    if secrets.randbelow(1000) > 980:
      #Random drop between 0 and 199
      value = secrets.randbelow(200)
      #Shows that there was money dropped
      await message.channel.send(embed=discord.Embed(title='{0} {1} were dropped'.format(str(value), currency_type)))
      #Logs the drop so it can be picked later
      redis_server.hset('drop.'+str(message.channel.id), str(message.id).encode('utf-8'), str(value).encode('utf-8'))
      #Resets the last drop time
      redis_server.set('last.drop', str(round(time.time(), None)).encode('utf-8'))

        
client.run(os.getenv('bot_token'))