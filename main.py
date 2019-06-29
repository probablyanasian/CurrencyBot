import discord
import redis
import os
import asyncio
import time
import secrets
import default_shop
import collections

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

#Need to run to init every startup.
change_prefix()

#Change the currency name
def change_currency():
  global currency_type
  if redis_server.exists('current.currency'):
    #use newly/currently set currency 
    currency_type = redis_server.get('current.currency').decode('utf-8')
  else: 
    redis_server.set('current.currency', 'dollars')
    currency_type = redis_server.get('current.currency').decode('utf-8')

#Need to run to init every startup.
change_currency()

#sets db to default values
def default_all(channel):
  change_prefix()
  change_currency()
  reset_store(channel)
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

def reset_store(channel):
  for store_type in ['Guild', 'House', 'Item']:
    for single_keys in redis_server.hkeys('custom.shop.'+store_type):
      redis_server.hdel('custom.shop.'+str(channel.guild.id)+'.'+store_type, single_keys)
  for item in default_shop.defaults:
    redis_server.hset('custom.shop.'+str(channel.guild.id)+'.Item', item, default_shop.defaults[item])
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

  if str(message.author.id) in os.getenv('owner_id'):
    if message.content == 'cur_bot_reset_all':
      default_all(message.channel)
      await message.channel.send(embed=discord.Embed(title=str(message.author), description="Reset to defaults"))
  
  #check for prefix first
  if message.content.startswith(prefix_char):
    uinput = str(message.content).split(" ", 1)
    command = uinput[0].strip(prefix_char)

    #try to isolate params, may be NULL
    try:
      params = uinput[1]
    except IndexError:
      params = ''
    
    channel = message.channel
    #Author details
    #author name str(message.author)
    #uname only str(message.author).rsplit("#", 1)[0]
    #discriminator str(message.author.discriminator)
    #author id str(message.author.id)


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

    elif command == 'pick':
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
    
	
    #Help command
    elif command == 'help':
      embed=discord.Embed(title="Command List", color=0x00ffff)
      await channel.send(embed=embed)
      
    #Store commands
    elif command in ['shop', 'store', 'itemshop', 'guildshop', 'shopguild', 'servershop', 'houses', 'house']:
      shop_type = None
      params_low = params.lower() 
      if params_low != '':
        if params_low in ['server', 'guild']:
          shop_type = 'Guild'
        elif params_low in ['house', 'homes', 'houses']:
          shop_type = 'House'
        elif params_low in ['items', 'item']:
          shop_type = 'Item'
      else:
        shop_type = 'Item'
        if command in ['guildshop', 'shopguild', 'servershop']:
          shop_type = 'Guild'
        elif command in ['houses', 'house']:
          shop_type = 'House'
      if shop_type != None:
        cur_shop = redis_server.hgetall('custom.shop.'+str(channel.guild.id)+'.'+shop_type)
        shop_items = list(cur_shop)
        item_count = len(shop_items)
        #Create embed
        embed=discord.Embed(title=shop_type+' Shop', color=0xff15e6)
        for iter in range(item_count):
          #ensure max of 9 objects, TODO have to paginate
          if iter <= 8:
            #add embed items
            if shop_items[iter].decode('utf-8') == 'roleitem':
              rolename = message.guild.get_role(int(cur_shop[shop_items[iter]].decode('utf-8'))).name
              itemcost = redis_server.hget('custom.shop.'+str(channel.guild.id)+'.Guild.role', int(cur_shop[shop_items[iter]])).decode('utf-8')
              embed.add_field(name='#'+str(iter+1)+' - '+str(rolename)+' Role', value=str(itemcost)+' '+currency_type, inline=True)
            else:
              embed.add_field(name='#'+str(iter+1)+' - '+' '.join(shop_items[iter].decode('utf-8').capitalize().split('_')), value=cur_shop[shop_items[iter]].decode('utf-8')+' '+currency_type, inline=True)
        #send
        await channel.send(embed=embed)
      else:
        #if params are weird
        await channel.send(embed=discord.Embed(title=str(message.author), description='Parameter not understood.'))

    elif command in ['buy', 'buyhouse', 'buyrole']:
      split_params = params.split(' ', 2) #shop_type item_reference_style item
      params_low = split_params.pop(0).lower()
      if params_low != '':
        if params_low in ['role', 'guilditem']:
          shop_type = 'Guild'
        elif params_low in ['house', 'homes', 'houses']:
          shop_type = 'House'
        elif params_low in ['items', 'item']:
          shop_type = 'Item'
      else:
        shop_type = 'Item'
        if command in ['buyrole', 'servershop']:
          shop_type = 'Guild'
        elif command in ['houses', 'house']:
          shop_type = 'House'

      if shop_type != None:
        cur_shop = redis_server.hgetall('custom.shop.'+str(channel.guild.id)+'.'+shop_type)
        shop_items = list(cur_shop)

        if len(split_params) == 1 or split_params[0] in ['num', 'itemnum', 'number']:
          if split_params[0] in ['num', 'itemnum', 'number']:
            split_params.pop(0)
          if shop_type == 'Guild':
            if shop_items[int(split_params[0])-1].decode('utf-8') == 'roleitem':
              rolename = message.guild.get_role(int(cur_shop[shop_items[int(split_params)-1]].decode('utf-8'))).name
              itemcost = redis_server.hget('custom.shop.'+str(channel.guild.id)+'.Guild.role', int(cur_shop[shop_items[int(split_params[0])-1]])).decode('utf-8')
            else:
              price = int(cur_shop[shop_items[int(split_params[0])-1]].decode('utf-8'))
              author_money = int(redis_server.get('id.'+str(message.author.id)).decode('utf-8'))
              if author_money >= price:
                redis_server.set('id.'+str(message.author.id), str(author_money-price).encode('utf-8'))
                await channel.send(embed=discord.Embed(title=str(message.author), description='You bought a {0} for {1} {2}'.format(shop_items[int(split_params[0])-1].decode('utf-8'), price, currency_type)))
              else:
                await channel.send(embed=discord.Embed(title='', description='**{0}** You don\'t have enough {1}'.format(str(message.author), currency_type)))
          if shop_type == 'House':
            price = int(cur_shop[shop_items[int(split_params[0])-1]].decode('utf-8'))
            author_money = int(redis_server.get('id.'+str(message.author.id)).decode('utf-8'))
            if author_money >= price:
              redis_server.set('id.'+str(message.author.id), str(author_money-price).encode('utf-8'))
              await channel.send(embed=discord.Embed(title=str(message.author), description='You bought a {0} for {1} {2}'.format(shop_items[int(split_params[0])-1].decode('utf-8'), price, currency_type)))
            else:
              await channel.send(embed=discord.Embed(title='', description='**{0}** You don\'t have enough {1}'.format(str(message.author), currency_type)))

          if shop_type == 'Item':
            try:
              price = int(cur_shop[shop_items[int(split_params[0])-1]].decode('utf-8'))
              author_money = int(redis_server.get('id.'+str(message.author.id)).decode('utf-8'))
              if author_money >= price:
                redis_server.set('id.'+str(message.author.id), str(author_money-price).encode('utf-8'))
                await channel.send(embed=discord.Embed(title=str(message.author), description='You bought a {0} for {1} {2}'.format(shop_items[int(split_params[0])-1].decode('utf-8'), price, currency_type)))
              else:
                await channel.send(embed=discord.Embed(title='', description='**{0}** You don\'t have enough {1}'.format(str(message.author), currency_type)))
            except IndexError:
      else:
        await channel.send(embed=discord.Embed(title=str(message.author), description='Unknown Parameter'))

    #Add items to store namely role items
    elif message.author.permissions_in(channel).manage_roles:
      if command in ['storeadd', 'shopadd']:
        split_params = params.split(' ', 2) #type cost name
        if len(split_params) == 2 or split_params[0] in ['items', 'item']:
          if split_params[0] in ['items', 'item']:
            split_params.pop(0) #Delete the item "item_type"
          try:
            if int(split_params[0]) >= 0:
              redis_server.hset('custom.shop.'+str(channel.guild.id)+'.Guild', split_params[1].encode('utf-8'), split_params[0].encode('utf-8'))
              embed=discord.Embed(title=str(message.author), description='Guild item {0} added successfully at {1} {2}'.format(split_params[1], split_params[0], currency_type))
              await channel.send(embed=embed)
          except ValueError:
            await channel.send(embed=discord.Embed(title=str(message.author), description='First parameter should be a number'))
        elif split_params[0] in ['roles', 'role']:
          try:
            if int(split_params[1]) >= 0:
              role_id = int("".join(filter(lambda char: char not in "<&@>", split_params[2])))
              if message.guild.get_role(role_id).id != None:
                redis_server.hset('custom.shop.'+str(channel.guild.id)+'.Guild.role', role_id, split_params[1].encode('utf-8'))
                redis_server.hset('custom.shop.'+str(channel.guild.id)+'.Guild', 'roleitem'.encode('utf-8'), role_id)
                embed=discord.Embed(title=str(message.author), description='Guild roleitem {0} added successfully at {1} {2}'.format(split_params[2], split_params[1], currency_type))
                await channel.send(embed=embed)
              else:
                await channel.send(embed=discord.Embed(title=str(message.author), description='Role not found'))
          except ValueError:
            await channel.send(embed=discord.Embed(title=str(message.author), description='Incorrect Parameters'))
        else:  
          await channel.send(embed=discord.Embed(title=str(message.author), description='Requires 2-3 parameters'))

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
          default_all(message.channel)
       
      elif command == 'changeprefix':
        redis_server.set('current.prefix', params)
        change_prefix()
        await channel.send(embed=discord.Embed(title=str(message.author), description='Prefix changed to {0}'.format(params)))

      elif command == 'changecurrency':
        redis_server.set('current.currency', params)
        change_currency()
        await channel.send(embed=discord.Embed(title=str(message.author), description='Currency changed to {0}'.format(params)))

      elif command == 'award':
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

      elif command == 'shutdown':
        await client.logout()
        await client.close()

  #On a noncommand, every 3 minutes
  elif (round((time.time()), None) - int(redis_server.get('last.drop').decode('utf-8'))) > 180:
    #2 percent chance
    if secrets.randbelow(1000) < 20:
      #Random drop between 0 and 199
      value = secrets.randbelow(200)
      #Shows that there was money dropped
      await message.channel.send(embed=discord.Embed(title='{0} {1} were dropped'.format(str(value), currency_type)))
      #Logs the drop so it can be picked later
      redis_server.hset('drop.'+str(message.channel.id), str(message.id).encode('utf-8'), str(value).encode('utf-8'))
      #Resets the last drop time
      redis_server.set('last.drop', str(round(time.time(), None)).encode('utf-8'))

        
client.run(os.getenv('bot_token'))