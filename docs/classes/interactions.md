### [humecord](../..)/[docs](../README.md)/[classes](./README.md)/interactions

---
# events

class: `humecord.classes.interactions.Interactions`

instance: `humecord.bot.interactions`

---
Handles registration and callback of discord interactions.

## user documentation
You're probably looking for the **[components documentation](../utils/components.md)**. This document is only the technical outline for how interactions are internally handled.

## outline
* **.register_component(_type: str, _id: str, callback: \*function, author: \*int, \*permanent: bool = False)**

    Registers a component to the interaction store for future callback.

    Note that anything that is not a permanent interaction will not be retained after a bot restart.

    *Arguments:*
    - `_type`: Type of component
    - `_id`: Custom ID for component
    - `callback`: Function, leading to async function, to call on reciept
    - `author`: Author to listen for interactions from
    - `permanent`: Whether or not the interaction is permanent/persistent across restarts or timeouts
    
    *Raises:*
    - `InvalidComponent`: Component info sent is not valid

* **.remove_expired()**

    Removes all expired interactions from memory.

* **async .recv_interaction(interaction: discord.Interaction, \*perma_override: bool = False)**

    Receives, processes, and sends the callback for an interaction.

    *Arguments:*
    - `interaction`: Interaction to process.
    - `perma_override`: Whether or not the component should be processed as permanent