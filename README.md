mdexe
=====

It can execute a code written in a fence block in a markdown document.

NOTE: not recommend to put critical code in the snipet block.

## How to use

```
git clone https://github.com/tanupoo/mdexe
cd mdexe
```

Then, just type `mdexe.py README.md` in the directory you cloned.
It means that mdexe.py will parse the README.md file you are reading.
You can see the snipets and the identifier of each snipet like below.

```
## SNIPET: ID:1 LANG:python NAME:None

01: print("an example of Phthon")

## SNIPET: ID:2 LANG:node NAME:None

01: console.log("an example of Node.js.")

## SNIPET: ID:3 LANG:perl NAME:None

01: print "an example of Perl.\n"

## SNIPET: ID:4 LANG:sh NAME:None

01: echo "an example of shell."

## SNIPET: ID:5 LANG:php NAME:None

01: print("an example of PHP.");

## SNIPET: ID:6 LANG:python NAME:None

01: def sample_one():
02:     print("one")
03:
04: sample_one()
05:
06: def sample_two():
07:     print("two")
08:
09: sample_two()

## SNIPET: ID:7 LANG:python NAME:one

01: def sample_one():
02:     print("one")
```

You can specify the id by the -i option, and execute it with the -x option.
For example, if you want to run the 1st one, which is witten by Python.

```
% mdexe.py README.md -i 1 -x

## SNIPET: ID:1 LANG:python NAME:None

01: print("an example of Phthon")

## RESULT: ID:1 LANG:python NAME:None

an example of Phthon
```

You will see the result of the 3rd snipet
that is written in Javascript in this README.md.

Please be sure that python has been installed in this case.
If you see the error like below, maybe python is not included in your PATH.

```
FileNotFoundError: [Errno 2] No such file or directory: 'python'
```

## Sample code in the markdown.

```python
print("an example of Phthon")
```

```js
console.log("an example of Node.js.")
```

```perl
print "an example of Perl.\n"
```

```sh
echo "an example of shell."
```

```awk
print "an example of awk BEGIN section."
```

```php
print("an example of PHP.");
```

## Exceptions

In the case of the anipet of awk,
the code is executed as the one written in the BEGIN section.
If you want to put full awk snipet
such as containing the END section or the patter matching,
you can put it as the shell snipet.

````
```sh
echo "Hello awk." | awk '
{ print toupper($0); }
END {
    print strftime("%M:%S", systime())
    print "--- mdexe"
}
'
```
````

## Tweaks.

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
