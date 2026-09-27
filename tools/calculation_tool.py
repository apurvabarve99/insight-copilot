def calculate_sum(values):
    """
    Calculate the sum of a list of numeric values.
    """
    return sum(values)


def calculate_percentage_change(old_value, new_value):
    """
    Calculate percentage change between two values.
    """
    if old_value == 0:
        raise ValueError("Cannot calculate percentage change from zero.")

    percentage_change = (
        (new_value - old_value) / old_value
    ) * 100

    return percentage_change