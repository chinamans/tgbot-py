from libs import others
from pyrogram import filters, Client
from pyrogram.types.messages_and_media import Message


def calc_starting_bet(c=50000000, max_n=20):
    
    lines = []
    header = f"{'连输次数':<6} | {'起手金额':>10} | {'最后一注':>10} | {'总投入':>15}"
    separator = "-" * len(header)
    lines.append(header)
    lines.append(separator)

    for n in range(1, max_n + 1):
        power = 2 ** (n - 1)
        x = abs((c - (power - 1)) // power)
        last_bet = power * x + (power - 1)
        total = sum(2 ** i * x + (2 ** i - 1) for i in range(n))

        line = f"{n:<6} | {x:>10,} | {last_bet:>10,} | {total:>15,}"
        lines.append(line)

    return "\n".join(lines)
    



@Client.on_message(filters.me & filters.command("betbonus") )
async def calc_start_bet(client: Client, message: Message):
    if len(message.command) < 3:
        await message.reply("参数不足。用法：`/fanda lose/win/all on/off`")
        return
    cmd_name = message.command[0].lower()
    num = float(message.command[1]) if message.command[1].isdigit() else 0
    count = int(message.command[2]) if message.command[1].isdigit() else 1
    re_mess = calc_starting_bet(c=num, max_n=count)
    send_mess = await message.edit(f"```\n{re_mess}```")
    await others.delete_message(send_mess, 60)