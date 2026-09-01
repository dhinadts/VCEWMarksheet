from app.services.ocr.vcew_template import VCEW_INTERNAL_MARKSHEET


def test_vcew_model_exposes_only_sixteen_mark_fields():
    fields = VCEW_INTERNAL_MARKSHEET.fields()
    assert [field.field_name for field in fields] == [f"question_{number:02d}" for number in range(1, 17)]
    assert all(len(field.candidates) == 1 for field in fields[:10])
    assert all(field.option_labels == ("A", "B") for field in fields[10:])


def test_vcew_regions_stay_inside_marks_table_and_exclude_metadata():
    width, height = 1440, 1870
    cells = [region.to_cell(width, height, row=field.question_number, column=index)
             for field in VCEW_INTERNAL_MARKSHEET.fields()
             for index, region in enumerate(field.candidates)]
    assert VCEW_INTERNAL_MARKSHEET.matches(width, height)
    assert all(cell.y > height * 0.59 for cell in cells)
    assert all(cell.y + cell.height < height * 0.85 for cell in cells)
    assert all(cell.x < width * 0.71 for cell in cells)
