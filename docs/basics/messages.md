### [humecord](../..)/[docs](../README.md)/[basics](./README.md)/messages

---
# humecord basics
## using the messenger

The Humecord Messenger provides an easily adaptable way to send custom embeds and messages to users.

It allows you to define default values with placeholders in your `messages.yml` file, as well as allows users to override them with whatever content they want if you allow them to.

## configuration

Message defaults are editable in `messages.yml`.
```yml
sample: # category name
  sample: # subcategory name
    sample: # message name
      embed: # embed to send
        title: Sample message
        description: |
          This is a sample message, sent as an embed.
          Everything passed in this embed has placeholders filled in,
          then is passed as kwargs into utils.discordutils.create_embed.

        fields:
          - name: Here's a sample field
            value: |
              Here are some placeholders: %bot% %user% %other_placeholder%

        color: invisible

      text: | # text to send
        This is a sample message, sent as plaintext instead of an embed.

        I can use placeholders, too: %bot% %user% %other_placeholder%

        if[some_conditional]:::This line will only display if some_conditional is True.

        if[exists:bot]:::And, this will only display if 'bot' is not None.
        if[exists:user]:::Conditionals test

      placeholders: # placeholders available
        - bot
        - user
        - other_placeholder

      conditionals:
        some_conditional: false # (defaults)

      default: embed # or "str", if you want it to default to plaintext
                    # Guild admins can override this, as well as manual calls
                    # to the messenger - guild choices have priority, then
                    # call preferences, then this.

      allow_override: true # Set to false to disallow guild admins from overriding
      allow_type_override: false # Set to false if you don't want people changing 'default'
```

Users can edit this, as long as `allow_override` is set to `True`, using `!messages`.

## usage

Sending this message entails:
```py
await resp.send(
    **(
        await bot.messages.get(
            ctx.gdb, # Guild database
            ["sample", "sample", "sample"], # category, subcategory, message - path to message
            {"bot": "test", "user": 1234, "other_placeholder": "yes"}, # placeholders
            {"some_conditional": True}, # conditionals
            force_type = None, # Force either type -- none = both
            ext_placeholders = {}, # Extra placeholders
            overrides = {} # Overrides message: embed/content from default type
        )
    )
)
```