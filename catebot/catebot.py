#-----------------------------------------------
# Catebot for discord
# based on https://github.com/konohitowa/catebot but forked and  rewritten for Red by bencos17

#  /u/kono_hito_wa
# Originally based upon /u/mgrieger's VerseBot
#-----------------------------------------------


from pathlib import Path
import random
import re

import discord
from redbot.core import commands


class Catebot(commands.Cog):
    """Baltimore Catechism lookup commands."""

    FILE_PATTERN = re.compile(r"^bccd_(\d+)\.txt$", re.IGNORECASE)
    QA_PATTERN = re.compile(r"^(\d+)\. Q\. (.*?)\nA\. (.*?)(?=\n\d+\. Q\.|\Z)", re.S | re.M)

    def __init__(self, bot):
        self.bot = bot
        self.default_book = 2
        self.data_dir = Path(__file__).parent / "data"
        self.books = {}  # int -> dict[int, tuple[str, str]]
        self._load_all_books()

    def _load_all_books(self):
        self.books = {}
        if not self.data_dir.exists():
            return

        for file_path in sorted(self.data_dir.iterdir()):
            if not file_path.is_file():
                continue

            match = self.FILE_PATTERN.match(file_path.name)
            if not match:
                continue

            try:
                book_num = int(match.group(1))
            except ValueError:
                continue

            qa = self._parse_file(file_path)
            if qa:
                self.books[book_num] = qa

    def _parse_file(self, file_path: Path):
        try:
            text = file_path.read_text(encoding="utf-8")
        except Exception:
            return {}

        qa = {}
        for match in self.QA_PATTERN.finditer(text):
            try:
                number = int(match.group(1))
            except ValueError:
                continue

            question = " ".join(match.group(2).split())
            answer = " ".join(match.group(3).split())
            qa[number] = (question, answer)

        return qa

    def _resolve_book(self, book: int | None):
        if book is None:
            book = self.default_book
        return book, self.books.get(book, {})

    @commands.group(name="bccd")
    async def bccd(self, ctx):
        """Baltimore Catechism commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Use: bccd question <num> [book], bccd search <term> [book], bccd random [book], bccd count [book], bccd books, bccd reload")

    @bccd.command(name="books")
    async def books(self, ctx):
        """List available catechism books."""
        if not self.books:
            await ctx.send("No data files loaded. Put bccd_*.txt files in the cog data folder.")
            return

        available = ", ".join(str(b) for b in sorted(self.books))
        await ctx.send(f"Available books: {available}. Default: {self.default_book}.")

    @bccd.command(name="question")
    async def question(self, ctx, number: int, book: int | None = None):
        """Show question and answer by number. Defaults to book 2."""
        selected_book, qa = self._resolve_book(book)
        if not qa:
            await ctx.send(f"Book {selected_book} is not loaded.")
            return

        item = qa.get(number)
        if not item:
            await ctx.send(f"Question {number} not found in book {selected_book}.")
            return

        question, answer = item
        embed = discord.Embed(
            title=f"Baltimore Catechism Book {selected_book} - Q{number}",
            color=0x3498DB,
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=answer, inline=False)
        await ctx.send(embed=embed)

    @bccd.command(name="search")
    async def search(self, ctx, term: str, book: int | None = None):
        """Search question and answer text. Defaults to book 2."""
        selected_book, qa = self._resolve_book(book)
        if not qa:
            await ctx.send(f"Book {selected_book} is not loaded.")
            return

        lowered = term.lower()
        matches = []
        for number, (question, answer) in qa.items():
            if lowered in question.lower() or lowered in answer.lower():
                matches.append((number, question, answer))

        if not matches:
            await ctx.send(f"No results for '{term}' in book {selected_book}.")
            return

        lines = []
        for number, question, answer in sorted(matches)[:10]:
            lines.append(f"**{number}.** {question} - {answer}")

        await ctx.send("\n\n".join(lines))

    @bccd.command(name="random")
    async def random_question(self, ctx, book: int | None = None):
        """Show a random question. Defaults to book 2."""
        selected_book, qa = self._resolve_book(book)
        if not qa:
            await ctx.send(f"Book {selected_book} is not loaded.")
            return

        number = random.choice(list(qa.keys()))
        question, answer = qa[number]
        embed = discord.Embed(
            title=f"Baltimore Catechism Book {selected_book} - Q{number}",
            color=0x2ECC71,
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=answer, inline=False)
        await ctx.send(embed=embed)

    @bccd.command(name="count")
    async def count(self, ctx, book: int | None = None):
        """Count loaded questions. Defaults to book 2."""
        selected_book, qa = self._resolve_book(book)
        await ctx.send(f"Book {selected_book}: {len(qa)} questions loaded.")

    @bccd.command(name="reload")
    @commands.is_owner()
    async def reload_data(self, ctx):
        """Reload text files from the cog data folder (owner only)."""
        self._load_all_books()
        books = ", ".join(str(b) for b in sorted(self.books)) if self.books else "none"
        await ctx.send(f"Reloaded data. Books loaded: {books}.")
