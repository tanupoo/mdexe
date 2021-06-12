mdexe
=====

It executes code in a fence block in a markdown document.

## How to use

if you want to run the 3rd snipet.  You can use the option -s.

```
% mdexe.py -f README.md -s 3
```

You will see the result of the 3rd snipet
that is written in Javascript in this README.md.

NOTE: don't put critical code in the markdown.  It's your own risk.

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

## Usage

```
% mdexe.py -h
usage: mdexe.py [-h] [-l LANG] [-f INPUT_FILE] [-s SCRIPT_ID] [-A] [-M] [-S]

execute code picked from markdown by key.

optional arguments:
  -h, --help     show this help message and exit
  -l LANG        specify a language name. (default: None)
  -f INPUT_FILE  specify a filename containing code snipet. (default: None)
  -s SCRIPT_ID   specify the script identifier, separated by comma. (default:
                 None)
  -A             specify to execute all snipets. (default: False)
  -M             show output in markdown. (default: False)
  -S             show original script. (default: False)
```

