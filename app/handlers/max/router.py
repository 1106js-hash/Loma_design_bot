handlers = []


def register(handler):
    handlers.append(handler)


async def handle_message(ctx):

    text = (ctx.text or "").strip()
    state = ctx.state

    print(f"HANDLER INPUT: {text} | STATE: {state}")

    for handler in handlers:
        try:
            handled = await handler(ctx)
            if handled:
                print(f"HANDLED BY: {handler.__name__}")
                return
        except Exception as e:
            print(f"ERROR in {handler.__name__}: {e}")

    print("NO HANDLER TRIGGERED")