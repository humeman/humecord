### [humecord](../..)/[docs](../README.md)/[interfaces](./README.md)/files

---
# file interface

class: `humecord.interfaces.fileinterfaces.FileInterface`
instance: `humecord.bot.files`

---
This interface manages writing JSON data to files.

## user documentation

You're probably looking for the **[file interface documentation](../basics/files.md)**. This document is only the technical outline for how the file interface is used internally.

## outline

* **.write(name: str)**
    Writes a file to the disk.

    Arguments:
       - *name*: str - File name to write.
* **.files**
    Internal dict register of all active files.

    Format:
    ```py
    {
        "filename.json": {}, # file data
        "filename2.json": {},
        ...
    }
    ```