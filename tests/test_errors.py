from mlpproc import Preprocessor
from mlpproc.errors import PreprocessorError, PreprocessorWarning


def runtest_error(
    filename: str, in_text: str, error_name: str, error_line: int, error_char: int
) -> None:
    pre = Preprocessor()
    try:
        pre.process(in_text, filename)
    except PreprocessorError as err:
        assert (
            err.name == error_name and err.line == error_line and err.char == error_char
        )
        return
    assert False and "No error caught"


def runtest_warning(
    filename: str, in_text: str, error_name: str, error_line: int, error_char: int
) -> None:
    pre = Preprocessor()
    try:
        pre.process(in_text, filename)
    except PreprocessorWarning as err:
        assert (
            err.name == error_name and err.line == error_line and err.char == error_char
        )
        return
    assert False and "No error caught"


def test_error_preproc() -> None:
    test_warning = [
        ("{% ### %}", "invalid-command", 1, 0),
        ("{% undefined %}", "undefined-command", 1, 0),
    ]
    test_error = [
        ("{%", "unmatched-open-token", 1, 0),
        ("{% block %} {% if %} {% endblock %}", "unmatched-start-block", 1, 12),
        ("  %}", "unmatched-close-token", 1, 2),
    ]
    for in_text, name, line, char in test_warning:
        runtest_warning("test_error_preproc", in_text, name, line, char)
    for in_text, name, line, char in test_error:
        runtest_error("test_error_preproc", in_text, name, line, char)
