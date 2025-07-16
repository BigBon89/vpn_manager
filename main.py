import asyncio
import logging
import sys
from aiocryptopay import AioCryptoPay, Networks
from aiocryptopay.const import InvoiceStatus
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core import Core

dp = Dispatcher()

message_start = (
    "🔥 Наши серверы не имеют ограничений по скорости и трафику,"
)

message_instruction = (
    "Инструкция для вашей OS 👇\n\n"
)

core = Core()
bot = Bot(token=core.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
cryptopay = AioCryptoPay(token=core.crypto_pay_token, network=Networks.MAIN_NET)

@dp.message(CommandStart())
async def command_start(message: Message) -> None:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🛒 Приобрести", callback_data="callback_buy"),
        InlineKeyboardButton(text="📔 Инструкция", callback_data="callback_instruction"),
    )
    builder.row(
        InlineKeyboardButton(text="📡 Доступные серверы", callback_data="callback_servers"),
        InlineKeyboardButton(text="🔥 Моя подписка", callback_data="callback_my_sub"),
    )
    await message.answer(message_start, reply_markup=builder.as_markup())


@dp.callback_query(F.data == "callback_start")
async def callback_start(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🛒 Приобрести", callback_data="callback_buy"),
        InlineKeyboardButton(text="📔 Инструкция", callback_data="callback_instruction"),
    )
    builder.row(
        InlineKeyboardButton(text="📡 Доступные серверы", callback_data="callback_servers"),
        InlineKeyboardButton(text="🔥 Моя подписка", callback_data="callback_my_sub"),
    )
    await callback.message.edit_text(message_start, reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "callback_my_sub")
async def callback_my_sub(callback: CallbackQuery) -> None:
    message = "Ваша подписка:\n\n"
    builder = InlineKeyboardBuilder()
    user = callback.from_user.id
    key = core.db.get_key_from_tg_id(user)
    if key is None:
        message += "Подписка не найдена"
        builder.row(InlineKeyboardButton(text="🛒 Приобрести", callback_data="callback_buy"))
    else:
        message += f"Подписка заканчивается: {key.end}"
        builder.row(InlineKeyboardButton(text="🔑 Получить ключ", callback_data="callback_get_key"))
        builder.row(InlineKeyboardButton(text="🔄 Обновить ключ", callback_data="callback_update_key"))
        builder.row(InlineKeyboardButton(text="🛒 Продлить", callback_data="callback_buy"))

    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="callback_start"))
    await callback.message.edit_text(message, reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "callback_get_key")
async def callback_get_key(callback: CallbackQuery) -> None:
    message = core.db.get_key_from_tg_id(callback.from_user.id).url
    await callback.message.answer(f"<code>{message}</code>")
    await callback.answer()


@dp.callback_query(F.data == "callback_update_key")
async def callback_update_key(callback: CallbackQuery) -> None:
    user = callback.from_user.id
    core.db.update_key_url(user, await core.create_url(str(user)))
    await core.update_key(user)
    await callback_get_key(callback)


@dp.callback_query(F.data == "callback_buy")
async def callback_buy(callback: CallbackQuery) -> None:
    # if callback.from_user.id != core.admin_id:
        # await callback.answer()
        # return
    message = "🛒 Выберите нужный тариф ниже 👇🏻:\n\n"
    builder = InlineKeyboardBuilder()
    for plan in core.plans.plans:
        callback_data = f"callback_buy2_{plan.name}_{plan.price}"
        text = f"{plan.name} мес - {plan.price}₽"
        builder.row(InlineKeyboardButton(text=text, callback_data=callback_data))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="callback_start"))
    await callback.message.edit_text(message, reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("callback_buy2_"))
async def callback_buy2(callback: CallbackQuery) -> None:
    months, price = callback.data.removeprefix("callback_buy2_").split("_")
    message = "🛒 Выберите способ оплаты ниже 👇🏻:\n\n"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="CryptoBot", callback_data=f"callback_buy3_cryptobot_{months}_{price}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="callback_buy"))
    await callback.message.edit_text(message, reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("callback_buy3_"))
async def callback_buy3(callback: CallbackQuery) -> None:
    payment_method, months, price = callback.data.removeprefix("callback_buy3_").split("_")

    if payment_method == "cryptobot":
        invoice = await cryptopay.create_invoice(
            asset="USDT",
            amount=round((int(price) / 80) * 1.05, 2),
            payload=f"{callback.from_user.id}_{months}",
            expires_in=60 * 60 * 24,
            description=f"Подписка на {months} месяцев"
        )
        core.db.add_cryptopay(callback.from_user.id, invoice.invoice_id)
        await callback.message.answer(invoice.bot_invoice_url)
    await callback.answer()


async def payment_success(tg_id: int, months: int) -> None:
    await core.delete_depleted_clients()
    core.db.delete_depleted_keys()
    await core.add_key(tg_id, 30 * int(months))


@dp.callback_query(F.data == "callback_instruction")
async def callback_instruction(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="callback_start"))
    await callback.message.edit_text(
        message_instruction, disable_web_page_preview=True, reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "callback_servers")
async def callback_servers(callback: CallbackQuery):
    message = "Список наших серверов на текущий момент времени:\n\n"
    builder = InlineKeyboardBuilder()
    for server in core.servers.servers:
        message += f"{server.flag}{server.country} {server.city}\n"
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="callback_start"))
    await callback.message.edit_text(message, reply_markup=builder.as_markup())
    await callback.answer()


async def cryptobot_payment_check() -> None:
    invoice_ids = core.db.get_all_cryptopay_invoice_ids()
    if not invoice_ids:
        return
    invoices = await cryptopay.get_invoices(invoice_ids=invoice_ids)
    for invoice in invoices:
        if invoice.status != InvoiceStatus.PAID:
            continue
        tg_id, months = map(int, invoice.payload.split("_"))
        await payment_success(tg_id, months)
        core.db.delete_cryptopay_by_invoice(invoice.invoice_id)
        await bot.send_message(chat_id=tg_id, text=f"Оплата прошла успешно, вам начислено {months} месяцев")


async def payment_check() -> None:
    print("Payment check started")
    while True:
        await cryptobot_payment_check()
        await asyncio.sleep(10)


async def main() -> None:
    # await bot.delete_webhook(True)
    task_payment_check = None
    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        task_payment_check = asyncio.create_task(payment_check())
        await dp.start_polling(bot, polling_timeout=30)
    except Exception as e:
        print(e)
    finally:
        try:
            task_payment_check.cancel()
            await cryptopay.close()
            await bot.session.close()
        except Exception as e:
            print(e)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
    except Exception as e:
        print(e)