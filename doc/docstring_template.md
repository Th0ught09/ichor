# Template for Python Docstrings

```python
def add_integers(a: int, b: int) -> int:
    """ Add two integers together 
    
    :param a: The first integer to sum. If the explanation is longer
        that one line, then following lines of the explanation need to be
        indented so they are displayed correctly in the html docs.
    :param b: The second integer to sum
    :raises TypeError: If `a` or `b` are not integers, `TypeError` is raised.
    :return: The sum of the two integers `a` and `b`

    .. note::
        This is a note that will be outlined when making html documentation with sphinx
    """

    if not isinstance(a, int):
        raise TypeError(f"a is of type '{type(a)}' but should be type int")

    if not isinstance(b, int):
        raise TypeError(f"b is of type "{type(b)}" but should be type int")

    return a + b
```

If you use VS Code you can download the [Python Docstring extension](https://marketplace.visualstudio.com/items?itemName=njpwerner.autodocstring) which automatically generates docstrings from functions, classes, etc. once they have already been written. In order to make them in Sphinx format, add the
`"autoDocstring.docstringFormat": "sphinx"` settings in the VS Code settings (File -> Precerences -> Settings). Below is an example docstring that was generated by this extension. Since type annotations can be used, the types do not necessarily need to be specified in the docstring itself. More examples of Sphinx docstrings can be found [here](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html).

```python
def add_integers(a: int, b: int) -> int:
    """[summary]

    :param a: [description]
    :type a: int
    :param b: [description]
    :type b: int
    :raises TypeError: [description]
    :raises TypeError: [description]
    :return: [description]
    :rtype: int
    """

    if not isinstance(a, int):
        raise TypeError(f"a is of type '{type(a)}' but should be type int")

    if not isinstance(b, int):
        raise TypeError(f"b is of type "{type(b)}" but should be type int")

    return a + b
```