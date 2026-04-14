# CateBot Information

## Overview

This is a fork of CateBot rewritten as a Red-DiscordBot cog 

The cog reads the existing text files from:

- `catebot/data/bccd_1.txt`
- `catebot/data/bccd_2.txt`
- `catebot/data/bccd_3.txt`
- `catebot/data/bccd_4.txt`

## Commands

- `[p]bccd books`
	Lists available books found in the cog data folder.

- `[p]bccd count [book]`
	Shows how many questions were loaded for a book.

- `[p]bccd question <number> [book]`
	Returns one question and answer pair.

- `[p]bccd random [book]`
	Returns a random question and answer pair.

- `[p]bccd search <term> [book]`
	Searches question and answer text and returns up to 10 matches.

- `[p]bccd reload`
	Owner-only command to reload data from files.

If `[book]` is omitted, the default is book `2`.

## Data format

Each data file should contain entries in this format:

1. `1. Q. <question text>`
2. `A. <answer text>`

The parser supports multi-line questions and answers and normalizes whitespace.

## Notes

- Existing data files were moved from `utils/` into `catebot/data/` without changing their content.
- This documentation intentionally removes Reddit-specific behavior and references as it is no longer relevant to the codebase.
