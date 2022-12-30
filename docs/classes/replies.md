### [humecord](../..)/[docs](../README.md)/[classes](./README.md)/replies

---
# replies

class: `humecord.classes.replies.Replies`

instance: `humecord.bot.replies`

---

The Reply Handler provides a convenient way to obtain responses to messages from users without having to deal with extra commands and typing.

It utilizes Discord's reply feature to allow a user to pass data on to a callback function you provide if they reply to the message you specified.

**DEPRECATION WARNING:** This is slowly being phased out in favor of Discord's modal system, available in Humecord 0.4.0. Learn more about those [here](../utils/components.md).

## overview

Creating a reply callback is simple:
```py
# Say we send a message somewhere.
# Define this discord.Message class as `msg` to pass to the reply handler later.
msg = await resp.send("Reply to this message")

# Define a callback to run when someone replies.
# This accepts mostly the same args as a command.run() function --
# aside from the 'data' argument at the end.
async def my_callback(
        message,
        resp,
        args,
        user,
        gdb,
        alternate_gdb,
        preferred_gdb,
        data
    ):

    await resp.send(
        f"Thanks for replying to my message!\nYou said: {message.content}\nYour message args: {args}\nData: {data}"
    )


# Tell the reply handler to register a reply.
bot.replies.add_callback(
    msg.id, # Message ID to watch for replies from
    message.author.id, # Require responses from message.author (pass None if anyone can reply)
    my_callback,
    data = {
        "testing": 123
    }, # Data to pass along to the callback: see above
    delete_after = True # Deletes the message callback after to save memory (useful if they only need to reply once)
)
```

In the above example, if I were to reply to the message `msg` with "Hello World!", the response would be:
```
Thanks for replying to my message!
You said: Hello World!
Your message args: ["Hello", "World!"]
Data: {"testing": 123}
```

## api reference

* **.add_callback(message_id: int, author_id: \*int, callback: Callable, data: \*dict = {}, delete_after: \*bool = True)**

    Registers a callback to a message.

    *Arguments:*
    - `message_id` (int): Message ID to watch for replies to
    - `author_id` (*int): Author ID to require replies for (optional: `None` = anyone can reply)
    - `callback` (Callable): Function returning a coroutine (`async def`) to call on reply
    - `data` (*dict): Optional dict of data to pass to callback
    - `delete_after` (*bool): Delete callback from memory once used

* **async .read_reply(message: discord.Message)**

    Checks a message against the callback database, and runs callback if valid.

    *Arguments:*
    - `message` (discord.Message): Message to check for replies