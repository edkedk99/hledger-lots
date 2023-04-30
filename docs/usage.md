::: mkdocs-click
    :module: hledger_lots.cli
    :command: cli
	:prog_name: hledger-lots
	:depth: 0
	:style: table
	:list_subcommands: True

## Environment Variables

Some options are suposed to be constant for your workflow. They can be set as *environment variables*. See below available options:

| env                     | equivalent option  | content      | default |
|-------------------------|--------------------|--------------|---------|
| LEDGER_FILE             | --file             | journal file | None    |
| HLEDGER\_LOTS\_AVG_COST | --avg-cost         | true\|false  | false   |
| HLEDGER\_LOTS\_CHECK    | --check/--no-check | true\|false  | false   |
| HLEDGER\_LOTS\_NO\_DESC | --no-desc          | <str\>       | None    |


