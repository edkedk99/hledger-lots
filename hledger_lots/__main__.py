from .cli import cli


def main():
    cli(obj=dict(), auto_envvar_prefix="HLEDGER_LOTS")


if __name__ == "__main__":
    main()
