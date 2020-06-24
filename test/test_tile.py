from ohsome2label import tile


def test_truncate():
    assert tile.truncate(12, 34) == (12, 34)


def test_truncate_xy():
    assert tile.truncate_xy(12, 34) == (12, 34)
