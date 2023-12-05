from uagents import Agent, Context

alice = Agent(name="Rishi", seed="alice recovery phrase")


@alice.on_event("startup")
async def say_hello(ctx: Context):
    ctx.logger.info(f"hello, my name is {ctx.name}")


@alice.on_event("message")
async def echo(ctx: Context):
    ctx.logger.info(f"received message: {ctx.message}")
    await ctx.send(message=ctx.message)


if __name__ == "__main__":
    alice.run()
