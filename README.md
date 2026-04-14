# CateBot Red Cog

CateBot rewritten as a Red-DiscordBot cog for Catechism lookups.

## What this provides

- A folder-based Red cog at `catebot/`
- Data files stored in `catebot/data/`
- Commands to query Baltimore Catechism questions and answers from local text files
- Commands to query Vatican II documents from local text files

## Cog layout

- `catebot/__init__.py`
- `catebot/catebot.py`
- `catebot/info.json`
- `catebot/data/bccd_1.txt`
- `catebot/data/bccd_2.txt`
- `catebot/data/bccd_3.txt`
- `catebot/data/bccd_4.txt`
- `catebot/data/vatican2/DV.txt` through `catebot/data/vatican2/IM.txt`

## Commands

- `[p]bccd books`
- `[p]bccd count [book]`
- `[p]bccd question <number> [book]`
- `[p]bccd random [book]`
- `[p]bccd search <term> [book]`
- `[p]bccd reload` (owner only)
- `[p]vii docs`
- `[p]vii quote <abbr> <paragraph>`
- `[p]vii search <term> [abbr]`
- `[p]vii count [abbr]`
- `[p]vii reload` (owner only)

`[book]` is optional and defaults to `2`.

`[abbr]` is one of `DV`, `LG`, `SC`, `GS`, `GE`, `NA`, `DH`, `AG`, `PO`, `AA`, `OT`, `PC`, `CD`, `UR`, `OE`, or `IM`.

## Notes

- The cog reads the existing catechism data files and does not modify their contents.
- The cog also reads Vatican II documents from `catebot/data/vatican2/`.

## License

MIT License. See [LICENSE](LICENSE).
