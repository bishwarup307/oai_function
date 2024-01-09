import pytest

from oai_function.signature import detect_type


@pytest.parametrize("test_input,expected", [
    ["int", ("int", False)],
    ["float", ("float", False)],
    ["str", ("str", False)],
    ["bool", ("bool", False)],
    ["int|float", ("int|float", False)],
    ["int|float|str", ("int|float|str", False)],
    ["int|float|str|bool", ("int|float|str|bool", False)],
    ["Optional[int]", ("int", True)],
    ["Optional[float]", ("float", True)],
    ["int|None", ("int", True)],
    ["float | None", ("float", True)],
    ["Union[int, float]", ("int|float", True)],
    ["Union[int, float, str]", ("int|float|str", True)],
    ["List[int]", ("List[int]", False)],
    ["List[float]", ("List[float]", False)],
    ["Dict[str, int]", ("Dict[str, int]", False)],
    ["List[int|float]", ("List[int|float]", False)],
    ["List[Optional[int]]", ("List[int]", False)],
    ["Annotated(int, 'Some description')", ("int", False)],
])
def test_detect_type(test_input, expected):
    assert detect_type(test_input) == expected
