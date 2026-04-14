from .catebot import Catebot


async def setup(bot):
    await bot.add_cog(Catebot(bot))
