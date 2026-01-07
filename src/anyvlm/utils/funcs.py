"""Provides generic utility functions"""


def sum_nullables(values: list[int | None]) -> int | None:
    """Helper function to sum nullable values. Handles the following scenarios:
        - All values are ints: returns sum of values
        - Some values are ints, some are `None`: Returns sum of non-None values
        - All values are are `None`: Returns `None`

    :param values: The list of values to sum
    :returns: The sum of all non-None values, or `None` (see above for details)
    """
    running_sum: int | None = None
    for value in values:
        if value is not None:
            running_sum = value if running_sum is None else running_sum + value
    return running_sum
