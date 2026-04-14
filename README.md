# CateBot Red Cog

CateBot rewritten as a Red-DiscordBot cog for Catechism lookups.

## What this provides

- A folder-based Red cog at `catebot/`
- Data files stored in `catebot/data/`
- Commands to query Baltimore Catechism questions and answers from local text files

## Cog layout

- `catebot/__init__.py`
- `catebot/catebot.py`
- `catebot/info.json`
- `catebot/data/bccd_1.txt`
- `catebot/data/bccd_2.txt`
- `catebot/data/bccd_3.txt`
- `catebot/data/bccd_4.txt`

## Commands

- `[p]bccd books`
- `[p]bccd count [book]`
- `[p]bccd question <number> [book]`
- `[p]bccd random [book]`
- `[p]bccd search <term> [book]`
- `[p]bccd reload` (owner only)

`[book]` is optional and defaults to `2`.

## Notes

- The cog reads the existing catechism data files and does not modify their contents.

## License
 MIT License (MIT)
