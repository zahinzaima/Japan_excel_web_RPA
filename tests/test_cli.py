import pytest

from main import build_parser, parse_mode


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["--clean-run"], ("clean-run", None)),
        (["--resume"], ("resume", None)),
        (["--resume-from", "custom-checkpoint"], ("resume-from", "custom-checkpoint")),
        (["--resolve-errors"], ("resolve-errors", None)),
    ],
)
def test_cli_modes_parse_correctly(argv, expected):
    parser = build_parser()
    args = parser.parse_args(argv)
    assert parse_mode(args) == expected


def test_cli_requires_exactly_one_mode():
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args([])

    with pytest.raises(SystemExit):
        parser.parse_args(["--clean-run", "--resume"])
