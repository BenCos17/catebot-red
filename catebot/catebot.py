#-----------------------------------------------
# Catebot for discord
# based on https://github.com/konohitowa/catebot but forked and rewritten for Red by bencos17

#  /u/kono_hito_wa
# Originally based upon /u/mgrieger's VerseBot
#-----------------------------------------------

from pathlib import Path
import random
import re

import discord
from redbot.core import commands


class Catebot(commands.Cog):
    """Baltimore Catechism and Vatican II lookup commands."""

    FILE_PATTERN = re.compile(r"^bccd_(\d+)\.txt$", re.IGNORECASE)
    QA_PATTERN = re.compile(r"^(\d+)\. Q\. (.*?)\nA\. (.*?)(?=\n\d+\. Q\.|\Z)", re.S | re.M)

    VATICAN_DOCS = {
        "DV": "Dei Verbum",
        "LG": "Lumen Gentium",
        "SC": "Sacrosanctum Concilium",
        "GS": "Gaudium et Spes",
        "GE": "Gravissimum Educationis",
        "NA": "Nostra Aetate",
        "DH": "Dignitatis Humanae",
        "AG": "Ad Gentes",
        "PO": "Presbyterorum Ordinis",
        "AA": "Apostolicam Actuositatem",
        "OT": "Optatam Totius",
        "PC": "Perfectae Caritatis",
        "CD": "Christus Dominus",
        "UR": "Unitatis Redintegratio",
        "OE": "Orientalium Ecclesiarum",
        "IM": "Inter Mirifica",
    }

    VATICAN_PARAGRAPH_PATTERN = re.compile(
        r"(?ms)^(\d+)\.\s*(.*?)(?=^\d+\.\s|^CHAPTER\s+[IVXLC]+\s*$|^NOTES\s*$|\Z)"
    )

    def __init__(self, bot):
        self.bot = bot
        self.default_book = 2
        self.data_dir = Path(__file__).parent / "data"
        self.books = {}  # int -> dict[int, tuple[str, str]]
        self.vatican_docs = {}  # str -> dict[int, str]
        self._load_all_books()
        self._load_vatican_docs()

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

            qa = self._parse_bccd_file(file_path)
            if qa:
                self.books[book_num] = qa

    def _parse_bccd_file(self, file_path: Path):
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

    def _load_vatican_docs(self):
        self.vatican_docs = {}
        vatican_dir = self.data_dir / "vatican2"
        if not vatican_dir.exists():
            return

        for abbr, title in self.VATICAN_DOCS.items():
            file_path = vatican_dir / f"{abbr}.txt"
            if not file_path.is_file():
                continue

            paragraphs = self._parse_vatican_file(file_path)
            if paragraphs:
                self.vatican_docs[abbr] = paragraphs

    def _parse_vatican_file(self, file_path: Path):
        try:
            text = file_path.read_text(encoding="utf-8")
        except Exception:
            return {}

        paragraphs = {}
        for match in self.VATICAN_PARAGRAPH_PATTERN.finditer(text):
            try:
                number = int(match.group(1))
            except ValueError:
                continue

            paragraph_text = " ".join(match.group(2).split()).strip()
            if paragraph_text:
                paragraphs[number] = paragraph_text

        return paragraphs

    def _resolve_book(self, book: int | None):
        if book is None:
            book = self.default_book
        return book, self.books.get(book, {})

    def _resolve_vatican_doc(self, abbr: str):
        abbr = abbr.upper()
        return abbr, self.vatican_docs.get(abbr, {})

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
        self._load_vatican_docs()
        books = ", ".join(str(b) for b in sorted(self.books)) if self.books else "none"
        docs = ", ".join(sorted(self.vatican_docs)) if self.vatican_docs else "none"
        await ctx.send(f"Reloaded data. Books loaded: {books}. Vatican II docs loaded: {docs}.")

    @commands.group(name="vii", aliases=["vatican2", "vat2"])
    async def vii(self, ctx):
        """Vatican II document commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Use: vii docs, vii quote <abbr> <paragraph>, vii search <term> [abbr], vii count [abbr], vii reload")

    @vii.command(name="docs")
    async def vii_docs(self, ctx):
        """List available Vatican II documents."""
        if not self.vatican_docs:
            await ctx.send("No Vatican II files loaded. Put <abbr>.txt files in catebot/data/vatican2.")
            return

        lines = []
        for abbr in sorted(self.vatican_docs):
            title = self.VATICAN_DOCS.get(abbr, abbr)
            lines.append(f"**{abbr}** - {title} ({len(self.vatican_docs[abbr])} paragraphs)")
        await ctx.send("\n".join(lines))

    @vii.command(name="quote")
    async def vii_quote(self, ctx, abbr: str, number: int):
        """Quote a Vatican II paragraph by abbreviation and number."""
        doc_abbr, paragraphs = self._resolve_vatican_doc(abbr)
        if not paragraphs:
            available = ", ".join(sorted(self.vatican_docs)) if self.vatican_docs else "none"
            await ctx.send(f"Document {doc_abbr} is not loaded. Available docs: {available}.")
            return

        paragraph = paragraphs.get(number)
        if not paragraph:
            await ctx.send(f"Paragraph {number} not found in {doc_abbr}.")
            return

        title = self.VATICAN_DOCS.get(doc_abbr, doc_abbr)
        embed = discord.Embed(
            title=f"{doc_abbr} - {title} - Paragraph {number}",
            description=paragraph,
            color=0x3498DB,
        )
        await ctx.send(embed=embed)

    @vii.command(name="search")
    async def vii_search(self, ctx, term: str, abbr: str | None = None):
        """Search Vatican II documents for a term."""
        docs = [abbr.upper()] if abbr else sorted(self.vatican_docs)
        docs = [doc for doc in docs if doc in self.vatican_docs]
        if not docs:
            await ctx.send("No Vatican II docs loaded.")
            return

        lowered = term.lower()
        matches = []
        for doc_abbr in docs:
            for number, paragraph in self.vatican_docs[doc_abbr].items():
                if lowered in paragraph.lower():
                    snippet = paragraph
                    if len(snippet) > 180:
                        snippet = snippet[:177].rsplit(" ", 1)[0] + "..."
                    matches.append((doc_abbr, number, snippet))

        if not matches:
            target = abbr.upper() if abbr else "all Vatican II documents"
            await ctx.send(f"No results for '{term}' in {target}.")
            return

        lines = []
        for doc_abbr, number, snippet in matches[:10]:
            title = self.VATICAN_DOCS.get(doc_abbr, doc_abbr)
            lines.append(f"**{doc_abbr} {number} - {title}**: {snippet}")
        await ctx.send("\n\n".join(lines))

    @vii.command(name="count")
    async def vii_count(self, ctx, abbr: str | None = None):
        """Count Vatican II documents or a specific document's paragraphs."""
        if abbr:
            doc_abbr, paragraphs = self._resolve_vatican_doc(abbr)
            if not paragraphs:
                await ctx.send(f"Document {doc_abbr} is not loaded.")
                return
            await ctx.send(f"{doc_abbr}: {len(paragraphs)} paragraphs loaded.")
            return

        total_paragraphs = sum(len(paragraphs) for paragraphs in self.vatican_docs.values())
        await ctx.send(f"{len(self.vatican_docs)} Vatican II documents loaded with {total_paragraphs} paragraphs total.")

    @vii.command(name="reload")
    @commands.is_owner()
    async def vii_reload(self, ctx):
        """Reload Vatican II documents from the cog data folder (owner only)."""
        self._load_vatican_docs()
        docs = ", ".join(sorted(self.vatican_docs)) if self.vatican_docs else "none"
        await ctx.send(f"Reloaded Vatican II data. Documents loaded: {docs}.")
