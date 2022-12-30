### [humecord](../..)/[docs](../README.md)/[basics](./README.md)/files

---
# file interface

This document outlines the usage of the file interface.

View the [technical overview](../interfaces/files.md) for an in-depth description of all methods and functions.

---

## overview

The File Storage System is Humecord's way of syncing and writing data in JSON files to the hard disk for permanent storage. For example, by default, bot status information, humecord backend info, and persistent loop information is stored using this system. You can also use it to store your own data however.

## example

Here's a quick demo:

* In config.yml, add a file to the file system.
*Define the file name, then a set of default keys and values for the file.*
```yml
# Extra files to dump into the data directory
#   through the file interface.
req_files: 
  sample.json: 
    my_dict: {}
    some_awesome_key: null
```

* Access the data within the file from some of your running code.
```py
# Code:
return bot.files.files["sample.json"]["some_awesome_key"]

# Output:
None

# ---

# Code:
return bot.files.files["sample.json"]

# Output:
{"my_dict": {}, "some_awesome_key": None}
```

* Change data within the file, then save the changes.
```py
# Change 'my_awesome_key', then save changes
bot.files.files["sample.json"]["my_awesome_key"] = "Hello world!"

bot.files.write("sample.json")
```

* Check the file again.
```py
# Code:
return bot.files.files["sample.json"]["some_awesome_key"]

# Output:
"Hello world!"
```

## api reference
[Click here](../interfaces/fileinterface.md) to view the API reference for the file interface.

## restrictions

The only restriction in the file interface as of Humecord 0.4 is that you cannot create files starting with or ending with two underscores (ex: \_\_file\_\_.json). These names are reserved for internal use.

Beware of writing too much data to one file, as well. Each time a file is written to the disk its JSON data must be dumped again, which can become a bit taxing if too much data is present. This is only likely to become an issue when the file is megabytes in size.