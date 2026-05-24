from ai.utils.schema import BoundingBox


def test_valid_bbox() -> None:
    bbox = BoundingBox(x_center=0.5, y_center=0.5, width=0.2, height=0.2)
    assert bbox.is_valid()
    assert bbox.to_yolo_line().startswith("0 0.500000")


def test_invalid_bbox() -> None:
    bbox = BoundingBox(x_center=1.2, y_center=0.5, width=0.2, height=0.2)
    assert not bbox.is_valid()
