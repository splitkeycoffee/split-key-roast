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


def now_time(str=True):
    """Get the current time and return it back to the app."""
    import datetime
    if str:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return datetime.datetime.now()


def paranoid_clean(query_value):
    """Takes in a user's query value and cleans it up to ensure we don't end
    up with something we can't account for.

    :param query_value: query value to clean up
    :type query_value: str
    :returns: string a clean value
    """
    if query_value == None:
        return ''

    remove = ['{', '}', '<', '>', '"', "'", ";"]
    for item in remove:
        query_value = query_value.replace(item, '')
    query_value = query_value.rstrip().lstrip().strip()
    return query_value
