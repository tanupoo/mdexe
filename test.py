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
    assert md.quotes[0].lang == "python"
    assert md.quotes[0].id == "1"

def test02():
    text = """
````python
this is a python snipet.
````
    """
    md = ReadMarkdown(text=text)
    print(md.quotes)
    assert md.quotes[0].lang == "python"
    assert md.quotes[0].id == "1"

test02()
