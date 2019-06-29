# CurrencyBot

## A discord bot made for Discord Hack Week 2019

### Starting:
    
- You'll need the following packages: 'discord.py', 'asyncio', 'dotenv', 'redis'

- You'll also need to set up [redis](https://redis.io/download)

- Just run `python3 main.py` and it should be up and running!

- After that, type in a chat where the bot can see `cur_bot_reset_all` to reset the database to original
    
## Commands:

### Out of debug mode:
```
Currency

.cur [none]/[id]/[username]/[username#discrim]: 0-1 parameter; Gets the current amount of money someone owns. <Default: self>
                                                Aliases: .$, .cur, .currency
                                                
.pick:                                          no parameters; Picks up money that's been dropped.


Store

.buy [item type] [item num] [number of items]:  0-3 parameters; Purchases the specified item. <Default: [item] [idk] [1]>
                                                <Default Item Types: 
                                                Guild: 'role', 'guilditem'
                                                House: 'house', 'houses', 'homes'
                                                Items: 'items', 'item'>
                                                Aliases: .buy, .buyhouse, .buyrole

.shop, .store, .itemshop:                       no parameters; Shows the item shop.

.shop house, .shop houses, .shop homes:         no parameters; Shows the houses shop.

.shop server, .shop guild, .guildshop,          no parameters; Shows the guild shop.
.shopguild, .servershop:


Miscellaneous

.getprefix:                                     no parameters, Works without the prefix as a static command <Default returns: '.'>


```

### Owner only:
```
flushdb:                                        no parameters; Clears the currently used RedisDB

award [value] [user]:                           2 parameters; Gives the specified [user] [value] money.

changeprefix [newprefix]:                       1 parameter; Changes to prefix to [newprefix]

changecurrency [newcurrency]:                   1 parameter; Changes to currency to [newcurrency]

cur_bot_reset_all:                              no prefix; sets all DBs with a default to their default states
```

### In debug mode:

```
teststore [key] [value]: 2 parameters; Tries to store a key-value pair into the Redis DB.
```

## Created by:
- Probably an Asian#0508 (Programming)
- perhapsacat#0348 (Art, also kept the programmer sane by helping)


*To the Discord judge/evaluator: Thank you for taking the time to look at our project!*

*P.S. If you guys have internships available, in the summer hopefully, please let me know.*

*P. P. S. I'm pretty close to Discord HQ* - Probably an Asian#0508
