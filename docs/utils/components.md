# components system

Components are the internal name for buttons, dropdowns, input fields, and any other message-level interactive field processed using Interactions. Humecord provides a simple interface for creating these components, attaching them to messages, and performing custom actions when they're clicked by a user. 

## overview

The utility function used to create components is `humecord.utils.components.`

Within this, you can use functions `create_button`, `create_dropdown`, and `create_textinput` to create various components (see below for specifics).

To attach components to a message, you first need a `discord.View` object. Humecord also provides an easy way to do this via `components.create_view[# list of components here #]`.

## example

So, here's an example:

```py
# define some components in a list
components = [
    components.create_button(
        message,
        label = "Sample button",
        id = "sample",
        style = "primary",
        callback = lambda *args: button_callback("sample argument", *args),
        row = 0,
        only_sender = True
    ),
    components.create_dropdown(
        message,
        placeholder = "Sample dropdown",
        id = "select",
        options = {
            "opt1": {
                "name": "Option 1",
                "emoji": "🤌",
                "description": "Pick this one."
            },
            "opt2": {
                "name": "Option 2",
                "emoji": "🤨",
                "description": "No, pick this one."
            }
        },
        row = 1,
        callback = lambda *args: dropdown_callback("another sample argument", "👍", *args),
        only_sender = True
    )
]

# send these components to a channel
await resp.send(
    embed = ...,
    view = components.create_view(components)
)

# callback functions given to components and called on interaction
async def button_callback(
        extra_arg, # The one defined in the lambda function above ("sample argument")
        message, # Same args that a command gets
        resp,
        args,
        udb,
        gdb,
        alternate_gdb,
        preferred_gdb
    ):

    await resp.send(
        "You clicked the button!"
    )

async def dropdown_callback(
        an_extra_arg, # "another sample argument"
        another_extra_arg, # "👍"
        message,
        resp,
        args,
        udb,
        gdb,
        alternate_gdb,
        preferred_gdb,
        values # list of options chosen in dropdown
    ):

    if len(values) == 0:
        await resp.send(
            "You didn't pick anything! :("
        )

    else:
        await resp.send(
            "You selected: " + ", ".join(values) # values is a list of option ids (the name of the dicts passed in 'options' arg to create_dropdown)
        )
```

A lot to take in. I get it. Here's the specifics:

## reference

### views

Views are a required container of components, used before sending to a channel. Humecord makes this a bit simpler: all you have to do is use the function `components.create_view()` with a list of components, and the rest is done for you.

For example:
```py
view = components.create_view(
    [
        button1,
        button2,
        dropdown,
        ...
    ]
)
```

*By default, views expire after 1 hour to preserve memory. To override this, pass the `timeout = int(seconds)` value as an argument.*

This view is passed to a [ResponseChannel](../classes/responsechannels.md) via `resp.send()` or `resp.edit()` under the `view` argument to pass it to a message.

Continuing our above example:

```py
await resp.send(
    "This is the message content."
    embed = discordutils.create_embed(title = "This is an embed."),
    view = view
)
```

__**components.create_view**__
**Returns:** discord.UI.View
**Raises:** Nothing
**Arguments:**
    * **components** (list): list of components to insert into view
    * **timeout** (int) = 3600: time after which view expires in memory

### buttons

Creating buttons is done entirely through the method `components.create_button`.

__**discordutils.create_embed()**__
**Returns:** discord.UI.Button
**Raises:** exceptions.InvalidComponent
**Arguments:**
    * **message**: discord.Message object reference to get data from (required only if `only_sender` is True, but recommended regardless)
    * **style** (str) = "primary": button style to use (one of `primary`, `secondary`, `success`, `danger`, or `url`)
    * **label** (str): button text presented to the user (only optional if `emoji` is set)
    * **id** (str): 12-char or less internal label for the button (must be unique to the view)
    * **callback** (function): async function that will be called on interaction (not a coroutine)
        * arguments: `message, resp, args, udb, gdb, alternate_gdb, preferred_gdb`
    * **url** (str): url for `url` type buttons -- style must be set to `url` for this to matter
    * **disabled** (bool) = False: disables button presses
    * **emoji** (str): discord emoji snowflake or unicode emoji to display beside the label
    * **only_sender** (bool) = True: refuses interactions from anyone but the sender
    * **row** (int) = 0: row number, 0-4
    * **permanent** (bool) = False: if permanent, keeps the component in memory forever. callback will *not* do anything -- you must catch an `hc_on_perma_interaction` event instead (see example below under **permanent components**)
    * **permanent_id** (str): string to refer to this interaction ID if permanent (see example below under **permanent components**) (only required if permanent is `True`)

### dropdowns

__**discordutils.create_dropdown()**__
**Returns:** discord.UI.Select
**Raises:** exceptions.InvalidComponent
**Arguments:**
    * **message**: discord.Message object reference to get data from (required only if `only_sender` is True, but recommended regardless)
    * **placeholder** (str): placeholder displayed to the user before they select something
    * **min_values** (int) = 1: minimum values selected
    * **max_values** (int) = 1: maximum values selected (defaults to 1 to allow only one choice)
    * **id** (str): 12-char or less internal label for the component (must be unique to the view)
    * **callback** (function): async function that will be called on interaction (not a coroutine)
        * arguments: `message, resp, args, udb, gdb, alternate_gdb, preferred_gdb, values`
        * `values` is a list of IDs of chosen options
    * **options** (dict[str, dict[str, str]]): a dictionary of dropdown options (up to 25)
        * dict is formatted as:
        ```py
        options = {
            "option1_id": {
                "name": "option 1", # 100 chars
                "emoji": "👍", # optional
                "description": "option 1.", # optional, 100 chars
                "default": True # optional, if True will be pre-selected
            },
            "option2_id": {...}
        }```
    * **row** (int) = 0: row number, 0-4, to place the dropdown on (a dropdown takes up an entire row -- ensure nothing else is on the row selected)
    * **only_sender** (bool) = True: refuses interactions from anyone but the sender
    * **permanent** (bool) = False: if permanent, keeps the component in memory forever. callback will *not* do anything -- you must catch an `hc_on_perma_interaction` event instead (see example below under **permanent components**)
    * **permanent_id** (str): string to refer to this interaction ID if permanent (see example below under **permanent components**) (only required if permanent is `True`)

### text inputs

Not yet implemented. Check back soon.

### permanent components

Every component described above can be set as permanent to make it never expire, allowing it to be processed indefinitely instead of within the 1 hour usually defined. This is a bit more complex than regular components, however.

To enable a permanent interaction, use the following with `create_button`, `create_dropdown`, or `create_textinput`:
```py
create_...(
    ...,
    permanent = True,
    permanent_id = "test"
)
```
This `permanent_id` is important -- it must be unique to ensure that this component is processed over other permanent components, and is what will be used to find the component later.

To process a permanent component interaction, you must capture the `hc_on_perma_interaction` event. You can use the following code snippet in the `__init__` method of a command, event, or loop. Place all your code in place of `await do_something()`.
```py
self.my_perma_id = "test"

if my_perma_id not in humecord.reg_permas:
    @humecord.event("hc_on_perma_interaction")
    async def handle_verification_call(int_perma_id, message, resp, user, udb, gdb):
        if int_perma_id != my_perma_id:
            return

        await do_something()

    humecord.reg_perms.append(my_perma_id)
```