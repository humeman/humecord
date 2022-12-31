### [humecord](../..)/[docs](../README.md)/[classes](./README.md)/messages

---
# messenger

class: `humecord.classes.messages.Messenger`

instance: `humecord.bot.messages`

---

The Humecord Messenger provides an easily adaptable way to send custom embeds and messages to users.

It allows you to define default values with placeholders in your `messages.yml` file, as well as allows users to override them with whatever content they want if you allow them to.

## user documentation
⚠️ **NOTE**: You're probably looking for the tutorial on **[how to use the messenger](../basics/messages.md)**. This document is only the technical outline for how the messenger works.

## outline
* **async .get(gdb, path, placeholders, conditions, force_type, ext_placeholders, overrides)**

  Gets kwargs for sending a formatted message.

  General usage is:
  ```py
  await resp.send(**(await bot.messages.get(...)))
  ```

  *Params:*
  - `gdb` (dict): Guild database, if applicable. Otherwise, send `{}`.
  - `path` (list[str]): A list of strings pointing to the message location in messages.yml.
  - `placeholders` (dict[str, str]): Any placeholders to format into the message.
  - `conditions` (dict): Conditions and their values. See [basics](../basics/messages.md) for how this works.
  - `force_type` (Optional[str] = None): If specified, the message will be sent in the format given. Either `message` or `embed`.
  - `ext_placeholders` (dict = {}): Extra placeholders to add.
  - `overrides` (dict = {}): Overrides any embed fields with the specified args.

  *Returns:*
  - `kwargs` (dict)