def to_bool(value):
    """
    Take in a value and convert it to a boolean type.

    :param value: string or int signifying a bool
    :type value: str
    :returns: converted string to a real bool
    """
    positive = ("yes", "y", "true",  "t", "1")
    if str(value).lower() in positive:
        return True
    negative = ("no",  "n", "false", "f", "0", "0.0", "", "none", "[]", "{}")
    if str(value).lower() in negative:
        return False
    raise Exception('Invalid value for boolean conversion: ' + str(value))