from bindtox.cli import build_parser


def test_cli_parser_accepts_descriptor_command():
    parser = build_parser()
    args = parser.parse_args(["descriptors", "--smiles", "CCO"])
    assert args.command == "descriptors"
    assert args.smiles == "CCO"
