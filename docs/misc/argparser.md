# argument parser

This document outlines how the HumeCord argument parser works. This system is used in a number of places to validate user input automatically - settings, the command argument validator, and so on. The system is also expandable via the imports file if you find something that's missing.

## basic outline

Arguments are generally basic python types, separated by commas.

For example, validating the string `"test"` against the following rules:
* `str`: Valid
* `int`: Invalid
* `str[len(1-3)]`: Invalid 
* `((str[len(1-4)])||(str[len(7-8)]))&&(str[includes(te,st)])`: Valid

## reference

Currently, the type list is as follows:

| Type        | Details                  | Arguments                                     |
|:-----------:| ------------------------ | --------------------------------------------- |
| str         | A string.                | len(), includes(), alnum(), regex(), in()     |
| int         | An integer.              | between(), greater(), less()                  |
| float       | A float.                 | between(), greater(), less()                  |
| number      | An integer or float.     | between(), greater(), less()                  |
| bool        | A boolean.               |                                               |
| list        | A list.                  | item()                                        |
| dict        | A dict.                  | key(), value()                                |
| channel     | A Discord channel.       | perms(), inguild(), type()                    |
| user        | A Discord user.          | canedit(), inguild()                          |
| perms       | A HumeCord perms string. | category(), has()                             |
| embed       | A Discord embed.         | has()                                         |
(More coming as I develop it)

## format

Each rule can have a type and a list of arguments, as so:
* `type[argument1,argument2,...]`

Types are various functions, coded specifically for the type (and listed above).

So, for example, to get a string with a length between 1 and 3:
* `str[len(1,3)]`

Or, to get a string that has a length between 1 and 10 and includes either "a" or "b":
* `str[len(1,10)&includes(a,b)]`

## chaining

Arguments can also be chained together with a set of statements.

As in any programming language, you can negate these extra arguments, allow either, require both, and so on:
* `&&`: and
* `||`: or
* `!`: not

For example, to get a string *or* an integer:
* `str||int`

Or, to get a string that has "te" or "st" in it, but *isn't* "test":
* `str[includes(te,st)]&&!str[in(test)]`

You can also use parenthesis to create sets of arguments. For example, to get a string that includes 'te' or 'st' and is between 1 and 3 characters, or a string that includes 'es' or 'tt':
* `(str[includes(te,st)]&&str[len(1,3)])||(str[includes(es,tt)])`
