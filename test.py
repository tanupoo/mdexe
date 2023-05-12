from ReadMarkdown import ReadMarkdown

def test00():
    text = """
```
this is not a snipet.
```
    """
    md = ReadMarkdown(text=text)
    """
    [Snipet(lang='python', name=None, name2=None, lib=False, text=['this is a
    python snipet.\n'], working=2, id='1')]
    """
    assert md.quotes == []

def test01():
    text = """
```python
this is a python snipet.
```
    """
    md = ReadMarkdown(text=text)
    assert md.quotes[0].id == "1"
    assert md.quotes[0].lang == "python"

def test02():
    text = """
````python
this is a python snipet.
````
    """
    md = ReadMarkdown(text=text)
    assert md.quotes[0].id == "1"
    assert md.quotes[0].lang == "python"

def test_not_snipet01():
    text = """
```
this is a fenced block.
```
    """
    md = ReadMarkdown(text=text)
    assert md.quotes == []

def test_not_snipet02():
    text = """
````
this is a fenced block.
````
    """
    md = ReadMarkdown(text=text)
    assert md.quotes == []

def test_not_snipet03():
    text = """
````
```python
this is a fenced block, not a python snipet,
```
````
    """
    md = ReadMarkdown(text=text)
    assert md.quotes == []

def test_tweak01():
    text = """
```
````python
this is a fenced block, not a python snipet,
````
```
    """
    md = ReadMarkdown(text=text)
    assert md.quotes == []

    text = """
```python
#%inc: third

if __name__ == "__main__":
    sample_three()

#%name:main
```

```python
#%lib
#%name:third
def sample_three():
    print("three")
```
    """
    md = ReadMarkdown(text=text)
    assert len(md.quotes) == 2
    assert md.quotes[0].id == "1"
    assert md.quotes[0].lang == "python"
    assert md.quotes[0].name == "main"
    assert md.quotes[0].lib is False
    assert md.quotes[1].id == 0
    assert md.quotes[1].lang == "python"
    assert md.quotes[1].name == "third"
    assert md.quotes[1].lib is True

test_tweak01()
