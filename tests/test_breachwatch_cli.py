from breachwatch.cli import build_parser


def test_breachwatch_cli_accepts_check_email_command():
    parser = build_parser()
    args = parser.parse_args(["check-email", "--email", "alex.chen@example.com", "--password", "winter2024!"])
    assert args.command == "check-email"
    assert args.email == "alex.chen@example.com"
