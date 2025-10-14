from sole_solutions.core.utils import clamp_height, inches_to_cm, clamp_weight_lb, paginate

def test_height_and_conversion():
    """Test height clamping and inches-to-cm conversion."""
    assert clamp_height(2, 20) == (3, 11)
    assert clamp_height(9, -1) == (8, 0)
    ft, inch = clamp_height(6, 2)
    cm = inches_to_cm(ft, inch)
    assert abs(cm - 188.0) < 1e-6

def test_weight_clamping():
    """Weight should stay within expected range."""
    assert clamp_weight_lb(10) == 60
    assert clamp_weight_lb(400) == 350
    assert clamp_weight_lb(180) == 180

def test_pagination_behavior():
    """Pagination should divide data into correct pages."""
    rows = [{"i": i} for i in range(250)]

    # First page
    page_rows, page_num, total = paginate(rows, 100, 0)
    assert len(page_rows) == 100 and page_num == 1 and total == 3

    # Last page
    page_rows, page_num, total = paginate(rows, 100, 2)
    assert [r["i"] for r in page_rows[:3]] == [200, 201, 202]

    # Out-of-range index should clamp
    page_rows, page_num, total = paginate(rows, 100, 999)
    assert page_num == 3

    # Empty list case
    empty, pn, tot = paginate([], 100, 0)
    assert empty == [] and pn == 0 and tot == 0
