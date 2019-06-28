A discord bot made for Discord Hack Week 2019

Starting:
    
    You'll need the following packages: 'discord.py', 'asyncio', 'dotenv', 'redis'

    You'll also need to set up (redis)<https://redis.io/download>

    Just run `python3 main.py` and it should be up and running!
    
Commands:

    Out of debug mode:
    ```
    cur [none]/[id]/[username]/[username#discrim]: 0-1 parameter; Gets the current amount of money someone owns <Default: self>

    .getprefix: no parameters, works without the prefix as a static command <Default returns: '.'>
    ```

    Owner only:
    ```
    flushdb: no parameters; Clears the currently used RedisDB
    ```

    In debug mode:

    ```
    teststore [key] [value]: 2 parameters; Tries to store a key-value pair into the Redis DB.
    ```

*To Discord person: If you guys have internships available, in the summer hopefully, please let me know.*

*I'm pretty close to Discord HQ*
