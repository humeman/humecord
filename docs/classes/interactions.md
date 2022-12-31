### [humecord](../..)/[docs](../README.md)/[classes](./README.md)/interactions

---
# interactions
class: `humecord.classes.interactions.InteractionManager`

instance: `humecord.bot.interactions`

---
Handles registration and callback of discord components and their interactions.

## user documentation
⚠️ **NOTE**: You're probably looking for the tutorial on **[how to create components](../basics/components.md)**. This document is only the technical outline for how the interaction handler works.

## outline
* **async .create_view(components)**:
    
    Generates a view from a list of components.
    
    *Params:*
    - `components` (List[discord.ui.Item]): Components

        Generate using one of:
        .create_button()
        .create_select()
        .create_modal()
        .create_textinput

    *Returns:*
    - `view` (discord.ui.View)
* **async .create_button(name, callback, row, perma, disabled, sender, label, style, emoji, url)**:

    Generates a button and registers a callback to it.
    
    *Params:*

    -> General component args
    * `name` (str): Component name/ID (20 chars or less) - unique per message
    * `callback` (Optional[Callable] = None): Async function to call (args: ctx, resp)
    
            Does nothing if component is permanent.

            Tip - extra args:

            `lambda *a: func(*a, "my_arg_1", 1234, ...)`

            `async def func(ctx, resp, my_arg_1, my_arg_2, ...)`
    * `row` (int): Row, 0-4, to place the item in (max 5 buttons/1 select per row)
    * `perma` (bool = False): Permanent or not

        (Need hc_on_perma_interaction event hook to receive)
    * `disabled` (bool = False): Disable the button
    * `sender` (Optional[discord.User, discord.Member]): Sender to restrict usage to

    -> Button specific args
    * `label` (str): User-facing button label
    * `style` (humecord.ButtonStyles): Button style

        PRIMARY, SECONDARY, SUCCESS, DANGER, URL
        or GRAY, BLUE, GREEN, RED, URL
    * `emoji` (Optional[str, discord.Emoji, discord.PartialEmoji]): Emoji to display before item
    * `url` (Optional[str]): URL to forward to. Style must be .URL, and callback will be ignored.
    
    *Returns:*
    * `button` (discord.ui.Button)
* **async .create_select(name, callback, row, perma, disabled, sender, placeholder, min_values, max_values, options)**:

    Generates a dropdown/select menu and registers a callback to it.
    
    *Params:*

    -> General component args
    * `name` (str): Component name/ID (20 chars or less) - unique per message
    * `callback` (Optional[Callable] = None): Async function to call (args: ctx, resp)

        Does nothing if component is permanent.

        Tip - extra args:

        `lambda *a: func(*a, "my_arg_1", 1234, ...)`

        `async def func(ctx, resp, my_arg_1, my_arg_2, ...)`
    * `row` (int): Row, 0-4, to place the item in (max 5 buttons/1 select per row)
    * `perma` (bool = False): Permanent or not

        (Need hc_on_perma_interaction event hook to receive)
    * `disabled` (bool = False): Disable the button
    * `sender` (Optional[discord.User, discord.Member]): Sender to restrict usage to

    -> Select specific args
    * `placeholder` (str): Description which is displayed before a value is selected
    * `min_values` (int = 1): Minimum options checked before callback is run
    * `max_values` (int = 1): Maximum options which can be checked at once
    * `options` (dict[str, dict[str, Any]] = {}): Dropdown options

        Format:
        ```py
        options = {
            "option_1": {
                "name": "Sample option",
                "description": "A really cool option.",
                "emoji": "👍", # Optional
                "default": True # Optional -- if True, it's selected at send. Defaults to False.
            }
        }
        ```

    *Returns:*
    - `select` (discord.ui.Select)

* **async .create_modal(name, callback, sender, title, components)**:

    Generates a modal from a list of components.
    
    *Params:*

    -> General component args
    * `name` (str): Component name/ID (20 chars or less) - unique per message
    callback (Optional[Callable] = None): Async function to call (args: ctx, resp)

        Does nothing if component is permanent.

        Tip - extra args:

        `lambda *a: func(*a, "my_arg_1", 1234, ...)`

        `async def func(ctx, resp, my_arg_1, my_arg_2, ...)`
    * `sender` (Optional[discord.User, discord.Member]): Sender to restrict usage to

    -> Select specific args
    * `title` (str): Title to display to user
    * `components` (list[discord.ui.Item]): Components to render

    *Returns:*
    * `modal` (discord.ui.Modal)

* **async .create_textinput(name, callback, sender, title, components)**:

    Generates a textinput.

    Must be used in a modal.
    
    *Params:*

    -> General component args
    * `name` (str): Component name/ID (20 chars or less) - unique per message

    -> Select specific args
    * `label` (str): Input label
    * `default` (Optional[str]): Default text
    * `placeholder` (Optional[str]): Placeholder string before anything is input
    * `required` (bool = False): Whether or not the textinput is required
    * `min_length` (int = 1): Minimum text length to submit
    * `max_length` (int = 128): Maximum text length to submit
    * `long` (bool = False): If True, turns into a paragraph style input

    *Returns:*
    * `modal` (discord.ui.Modal)

* **async .skip(\*args, \*\*kwargs)**:

    Placeholder function for dynamically generating callbacks which
    accepts any args and does nothing.