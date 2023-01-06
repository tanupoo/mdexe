mdexe
=====

It can execute a code written in a fence block in a markdown document.

## How to use

Just type `mdexe.py README.md` like below.  `%` denotes a shell prompt.

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

## How to define a Common part.

`#%name` can be used to define the name of the snipet.
You can inject the snipet into another snipet where `#%inc` is defined.
If you don't want to include a snipet to be listed, you can put `#%lib` into the snipet.

See below.

````
```python
#%inc:one

sample_one()

#%inc:two

sample_two()
```

```python
#%name:one
def sample_one():
    print("one")
```

```python
#%name:two
#%lib
def sample_two():
    print("two")
```
````

That's going to be:

```
def sample_one():
    print("one")

sample_one()

def sample_two():
    print("two")

sample_two()
```

Note that the snipet named **two** doens't include in the list of the snipets.

## BUG

In mac OS and python3.8 or newer,
a snipet including multiprocessing may not work.
if you change the start method into `fork`, it can.

print(flush=True) may not work.
