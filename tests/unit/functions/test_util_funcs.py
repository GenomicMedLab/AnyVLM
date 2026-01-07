from anyvlm.utils.funcs import sum_nullables


def test_sum_nullables():
    assert sum_nullables(2, 4) == 2 + 4
    assert sum_nullables(None, 7) == 7
    assert sum_nullables(142, None) == 142
    assert sum_nullables(None, None) is None
    assert sum_nullables(0, 0) == 0
    assert sum_nullables(0, None) == 0
    assert sum_nullables(None, 0) == 0
