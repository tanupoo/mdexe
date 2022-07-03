mdexe
=====

It executes code in a fence block in a markdown document.

## How to use

Just type `mdexe.py README.md` like below.  `%` is a shell prompt.

```
% mdexe.py README.md

## SNIPET_ID 0: python

print("an example executed by phthon")


## SNIPET_ID 1: php

print("an example executed by php.");


## SNIPET_ID 2: node

console.log("an example executed by node.js.")

```

You can see the identifier of each snipet.
If you want to run the 3rd snipet.
You can specify the id (zero origin) by the option -i,
and the option -x to execute the snipet.

```
% mdexe.py README.md -i 2 -x

## SNIPET_ID 2 Result: node

an example executed by node.js.

```

You will see the result of the 3rd snipet
that is written in Javascript in this README.md.

NOTE: DON'T PUT CRITICAL CODE.  IT'S YOUR OWN RISK.

## Sample code in the markdown.

```python
print("an example executed by phthon")
```

```php
print("an example executed by php.");
```

```js
console.log("an example executed by node.js.")
```

## Library

```python, inc:one,two
sample_one()
sample_two()
```

```python,name:one
def sample_one():
    print("one")
```

```python,name:two
def sample_two():
    print("two")
```

## BUG

In mac OS and python3.8 or newer,
a snipet including multiprocessing may not work.
if you change the start method into `fork`, it can.

## Usage

```
usage: mdexe.py [-h] [-i SNIPET_IDS] [-x] [-s] [-H] [input_file]

execute code picked from markdown by key.

positional arguments:
  input_file     specify a filename containing code snipet. '-' means stdin.
                 (default: None)

optional arguments:
  -h, --help     show this help message and exit
  -i SNIPET_IDS  specify the snipet IDs separated by comma, OR 'all'. It's
                 required when the -x option is specified. (default: None)
  -x             execute snipets specified the IDs seperated by a comma.
                 (default: False)
  -s             specify to show the snipets even when the -x option is
                 specified. (default: False)
  -H             with this option, disable to show each header.
```

