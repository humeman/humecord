### [humecord](../..)/[docs](../README.md)/[basics](./README.md)/components

---
# humecord basics
## creating components

This file outlines the procedure for creating components (ie: buttons, dropdown menus, modals, text inputs, so on) in Humecord.

## brief overview

When you send a message to a user, whether it be from a slash command, message command, or even webhook, a parameter is available called `view` which allows you to attach components to the bottom of the message.

A view is simply a container of components, and components are each individual button or dropdown you create.

When a user presses a button or selects something from a dropdown, Discord sends back an interaction (hence `bot.interactions`). You don't need to know much about that -- just know that when that does happen, Humecord will read all the necessary data from this interaction and run whatever callback function you have specified, much like the procedure when slash commands happen.

At the moment you can only attach buttons and selects (discord's internal term for dropdowns) to messages. If you use a modal (a popup window) you can add textinputs.

So, in short, when you want to add some buttons/dropdowns:
* Create callbacks for the buttons/dropdowns
* Create the buttons/dropdowns with `bot.interactions.create_[button/select]`
* Add them to a view with `bot.interactions.create_view`
* Send them to the user with `resp.send`

## usage

Components, buttons, and textinputs are created using a few helper functions in `bot.interactions.`

* **async .create_button()**: Creates a button
* **async .create_select()**: Creates a dropdown
* **async .create_textinput()**: Creates a textinput

Which are then stored in:
* **async .create_view()**: Creates a view out of buttons and dropdowns
* **async .create_modal()**: Creates a modal out of textinputs

Each of the functions involving buttons, selects, and textinputs take the following arguments at their core:
* `name` (str): A 1-20 character name for this component. It should be different than all the other components attached to the message (although this is not required).
* `callback` (Optional[Callable]): A callback function to run when the item is used. Like a command, it should be async and take the args `resp` and `ctx`.
* `row` (int = 0): A number from 0-4 telling Discord where to place the component below the message.
* `perma` (bool = False): If True, the component will persist across bot restarts. This is a bit more involved, and should only ever be used where absolutely necessary. Docs pending.
* `disabled` (bool = False): If True, the component will be grayed out and unusable.
* `sender` (Optional[discord.User, discord.Member]): If specified, only that user will be able to use the component.

Beyond that, **buttons** take the arguments:
* `label` (str): A 1-25 character user-facing label for the button
* `style` (humecord.ButtonStyles): The button's style/color. 
        humecord.ButtonStyles + PRIMARY, SECONDARY, SUCCESS, DANGER, URL (or, if you forget: GRAY, BLUE, GREEN, RED, URL)
* `emoji` (Optional[str, discord.Emoji]): Emoji to display on the button.
* `url` (Optional[str]): URL to redirect to if clicked. `style` must be `humecord.ButtonStyles.URL` and any `callback` will not work.

**Dropdowns** take the arguments:
* `placeholder` (str): Text displayed on the dropdown when nothing is selected
* `min_values` (int = 1): Minimum values selected before callback. 
* `max_values` (int = 1): Maximum values allowed to be selected.
* `options` (dict[str, dict[str, Any]]): Options.
    * Format:
    ```py
        options = {
            "option_1": {
                "name": "Sample option",
                "description": "A really cool option.",
                "emoji": "👍", # Optional
                "default": True # Optional -- if True, it's selected at send. Defaults to False.
            },
            ...
        }
        ```

And **textinputs** take the arguments:
**Dropdowns** take the arguments:
* `label` (str): Title displayed above the textinput.
* `default` (str): Text already set to the textinput at callback.
* `placeholder` (str): Text displayed if nothing is entered into the textinput.
* `min_length` (int = 1): Minimum allowed length of the input.
* `max_length` (int = 128): Maximum allowed length of the input.
* `long` (bool = False): If True, the textinput turns into a paragraph-style input

For a full list of the parameters for these functions, **check out the API docs for [the interaction manager](../classes/interactions.md)**.

## examples

Here's a quick example of creating a button:

```py
# Command callback
async def run(self, resp: humecord.ResponseChannel, ctx: humecord.Context) -> None:
    components = [
        await bot.interactions.create_button(
            name = "mybutton1",
            callback = self.callback1,
            label = "Click me!",
            style = humecord.ButtonStyles.SUCCESS
        ),
        await bot.interactions.create_button(
            name = "mybutton2",
            callback = self.callback2,
            label = "Don't click me.",
            style = humecord.ButtonStyles.DANGER
        )
    ]

    view = await bot.interactions.create_view(
        components
    )

    await resp.send(
        "Here are some buttons!",
        view = view
    )

async def callback1(self, resp: humecord.ResponseChannel, ctx: humecord.Context) -> None:
    await resp.edit( # Edits the message they clicked on
        "You clicked button 1! Woohoo!"
    )

async def callback2(self, resp: humecord.ResponseChannel, ctx: humecord.Context) -> None:
    await resp.edit(
        "Why did you do that? :("
    )
```

And a dropdown:
```py
# Command callback
async def run(self, resp: humecord.ResponseChannel, ctx: humecord.Context) -> None:
    options = {
        "option1": {
            "name": "Option 1",
            "description": "Click this one!",
            "emoji": "👍"
        },
        "option2": {
            "name": "Option 2",
            "description": "Don't click this one.",
            "emoji": "👎"
        }
    }

    components = [
        await bot.interactions.create_select(
            name = "mydropdown",
            callback = self.callback,
            placeholder = "Click here!",
            options = options
        )
    ]

    view = await bot.interactions.create_view(
        components
    )

    await resp.send(
        "Here is a dropdown!",
        view = view
    )

async def callback(self, resp: humecord.ResponseChannel, ctx: humecord.Context) -> None:
    # The user's chosen option(s) are available in ctx.values (a list of the names selected -- in this case, either option1 or option2).

    user_choice = ctx.values[0]

    if user_choice == "option1": 
        await resp.edit(
            "You clicked option 1! Woohoo!"
        )

    elif user_choice == "option2":
        await resp.edit(
            "Why did you do that? :("
        )

    else:
        await resp.edit(
            "This will never run."
        )
```

And finally, a modal:
*Note: Modals can only be run on interaction. To ensure this is the case, even for message commands, have the user click a button first, then reply with the modal.*
```py
# Command callback
async def run(self, resp: humecord.ResponseChannel, ctx: humecord.Context) -> None:
    components = [
        await bot.interactions.create_button(
            name = "mybutton1",
            callback = self.button_callback,
            label = "Click for modal!",
            style = humecord.ButtonStyles.SUCCESS
        )
    ]

    view = await bot.interactions.create_view(
        components
    )

    await resp.send(
        "Click the button!",
        view = view
    )

async def button_callback(self, resp: humecord.ResponseChannel, ctx: humecord.Context) -> None:
    components = [
        await bot.interactions.create_textinput(
            name = "usersname",
            label = "Your name",
            placeholder = "Type your name here.",
            required = True
        )
    ]

    modal = await bot.interactions.create_modal(
        name = "modal",
        callback = self.callback,
        sender = ctx.user, # Required
        title = "An example modal",
        components = components
    )

    await resp.send_modal(modal)

async def modal_callback(self, resp: humecord.ResponseChannel, ctx: humecord.Context) -> None:
    # Values are stored in 'ctx.modal_args', a dict with the key being the modal component's 'name' param and the value being the user's input as a string.

    await resp.send(
        f"Hi, {ctx.modal_args['usersname']}!"
    )
```

## important note
This file only contains some boilerplate examples. To see the full extent to which components can be used, **see the API docs for [the interaction manager](../classes/interactions.md)**.