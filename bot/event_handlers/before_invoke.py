async def before_invoke(ctx):
    await ctx.trigger_typing()
