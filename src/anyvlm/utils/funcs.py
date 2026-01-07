"""Provides generic utility functions"""


def sum_nullables(value_a: int | None, value_b: int | None) -> int | None:
    """Helper function to sum two nullable values. Handles the following scenarios:
        - Both values are ints: returns sum of value_a + value_b
        - One value is an int, the other is `None`: Returns the non-null value
        - Both values are `None`: Returns `None`

    :param value_a: The first value to sum
    :param value_b: The second value to sum
    :returns: The sum of both values, or `None` (see above for details)
    """
    if value_a is None and value_b is None:
        return None
    if value_a is None:
        return value_b
    if value_b is None:
        return value_a
    return value_a + value_b
