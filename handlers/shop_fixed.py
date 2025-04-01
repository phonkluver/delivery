"""
Handlers for shop users.
This module contains handlers for shop-specific commands and functions.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from config import ROLE_SHOP, ADMIN_CHAT_IDS
from keyboards.shop_kb import get_shop_main_keyboard
from storage.database import get_user_role, create_order, get_shop_orders, _read_database
from utils.timezone import is_working_hours, get_working_hours_message

logger = logging.getLogger(__name__)

# Create router
router = Router()


class OrderForm(StatesGroup):
    """States for order creation process"""
    customer_phone = State()
    city = State()
    delivery_address = State()
    payment_amount = State()
    confirmation = State()


async def shop_access_required(message: Message):
    """Check if user has shop role"""
    user_id = message.from_user.id
    role = await get_user_role(user_id)
    return role == ROLE_SHOP


@router.message(Command("neworder"), StateFilter("*"))
@router.message(F.text == "📦 Новый заказ", StateFilter("*"))
async def cmd_new_order(message: Message, state: FSMContext):
    """Handler for /neworder command to create a new delivery"""
    if not await shop_access_required(message):
        await message.answer("Эта команда доступна только магазинам. Пожалуйста, зарегистрируйтесь как магазин.")
        return
    
    # Информационно уведомляем о нерабочем времени, но позволяем создавать заказы
    if not is_working_hours():
        working_hours_msg = get_working_hours_message()
        await message.answer(
            f"ℹ️ <b>Информация о рабочем времени</b>\n\n"
            f"Текущее время выходит за пределы рабочего времени службы доставки (<b>10:00 - 20:00</b>).\n"
            f"{working_hours_msg}\n\n"
            f"Ваш заказ будет принят, но обработка может быть отложена до начала рабочего времени.",
            parse_mode="HTML"
        )
    
    await state.clear()
    
    # Создаем клавиатуру с кнопкой отмены
    cancel_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
    
    await message.answer(
        "📝 <b>Создание нового заказа</b>\n\n"
        "Пожалуйста, предоставьте информацию по шагам.\n"
        "В любой момент вы можете нажать кнопку <b>❌ Отмена</b>, чтобы прервать процесс.\n\n"
        "Шаг 1️⃣: Введите номер телефона клиента в формате +992XXXXXXXXX:",
        reply_markup=cancel_kb
    )
    await state.set_state(OrderForm.customer_phone)


@router.message(OrderForm.customer_phone)
async def process_customer_phone(message: Message, state: FSMContext):
    """Process customer phone number input"""
    # Простая проверка формата телефона (можно улучшить в будущем)
    phone = message.text.strip()
    
    # Проверка минимально допустимого формата телефона
    if not (phone.startswith('+') and len(phone) >= 8):
        await message.answer(
            "❌ Неверный формат номера телефона!\n\n"
            "Пожалуйста, введите номер в формате +992XXXXXXXXX"
        )
        return
    
    await state.update_data(customer_phone=phone)
    
    cancel_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
    
    await message.answer(
        "Шаг 2️⃣: Пожалуйста, укажите <b>город доставки</b>:",
        reply_markup=cancel_kb
    )
    await state.set_state(OrderForm.city)


@router.message(OrderForm.city)
async def process_city(message: Message, state: FSMContext):
    """Process city input"""
    city = message.text.strip()
    
    # Минимальная проверка города
    if len(city) < 2:
        await message.answer("❌ Название города слишком короткое.\n\nПожалуйста, введите корректное название города.")
        return
    
    await state.update_data(city=city)
    
    # Получаем информацию о магазине (название и телефон)
    user_id = message.from_user.id
    role = await get_user_role(user_id)
    
    if role != ROLE_SHOP:
        await message.answer("❌ Ошибка: У вас нет прав магазина.")
        await state.clear()
        return
    
    db = await _read_database()
    shop_info = None
    
    for user in db["users"]:
        if user["id"] == user_id and user["role"] == ROLE_SHOP:
            shop_info = user["username"]
            break
    
    if not shop_info:
        await message.answer("❌ Ошибка: Информация о магазине не найдена.")
        await state.clear()
        return
    
    # Название магазина хранится в поле username
    # Формат: "Название магазина | Телефон"
    shop_name = shop_info.split(" | ")[0]
    
    # Сохраняем название магазина
    await state.update_data(shop_name=shop_name)
    
    cancel_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
    
    await message.answer(
        f"📍 <b>Шаг 3️⃣:</b> Пожалуйста, введите <b>адрес доставки</b>: \n\n"
        f"ℹ️ <i>Заказ будет оформлен от имени магазина:</i> <b>{shop_name}</b>",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )
    await state.set_state(OrderForm.delivery_address)


@router.message(OrderForm.delivery_address)
async def process_delivery_address(message: Message, state: FSMContext):
    """Process delivery address input"""
    await state.update_data(delivery_address=message.text)
    
    cancel_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
    
    await message.answer(
        "Шаг 4️⃣: Пожалуйста, укажите <b>сумму к оплате</b> (в сомони), которую курьер должен получить от клиента:\n\n"
        "🔹 Например: 150 или 150.50\n"
        "🔹 Если нет оплаты, введите 0",
        reply_markup=cancel_kb
    )
    await state.set_state(OrderForm.payment_amount)


@router.message(OrderForm.payment_amount)
async def process_payment_amount(message: Message, state: FSMContext):
    """Process payment amount input"""
    payment_text = message.text.strip().replace(',', '.')
    
    try:
        payment_amount = float(payment_text)
        if payment_amount < 0:
            raise ValueError("Payment amount cannot be negative")
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите корректную сумму оплаты (число больше или равное 0).\n\n"
            "Примеры: 150 или 150.50"
        )
        return
    
    await state.update_data(payment_amount=payment_amount)
    
    # Get all data to prepare confirmation message
    data = await state.get_data()
    
    # Format payment amount with 2 decimal places
    payment_formatted = f"{data['payment_amount']:.2f}" if data['payment_amount'] > 0 else "Нет"
    
    # Prepare order confirmation message
    confirmation_msg = (
        "📋 <b>Пожалуйста, подтвердите детали заказа:</b>\n\n"
        f"📱 Телефон клиента: {data['customer_phone']}\n"
        f"🏙️ Город: {data['city']}\n"
        f"🏪 Название магазина: {data['shop_name']}\n"
        f"📍 Адрес доставки: {data['delivery_address']}\n"
        f"💰 Сумма к оплате: {payment_formatted} сомони"
    )
    
    # Create confirmation keyboard
    confirm_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Подтвердить"), KeyboardButton(text="❌ Отменить")]
    ], resize_keyboard=True)
    
    await message.answer(confirmation_msg, reply_markup=confirm_kb)
    await state.set_state(OrderForm.confirmation)


@router.message(OrderForm.confirmation)
async def process_order_confirmation(message: Message, state: FSMContext):
    """Process order confirmation"""
    if message.text.lower() == "❌ отменить" or message.text.lower() == "отменить":
        await state.clear()
        await message.answer(
            "❌ Создание заказа отменено.",
            reply_markup=await get_shop_main_keyboard()
        )
        return
    
    if message.text.lower() != "✅ подтвердить" and message.text.lower() != "подтвердить":
        await message.answer(
            "❓ Пожалуйста, используйте одну из кнопок для подтверждения или отмены заказа:\n"
            "✅ <b>Подтвердить</b> - для создания заказа\n"
            "❌ <b>Отменить</b> - для отмены заказа"
        )
        return
    
    # Информационно уведомляем о нерабочем времени, но позволяем создавать заказы
    if not is_working_hours():
        working_hours_msg = get_working_hours_message()
        await message.answer(
            f"ℹ️ <b>Информация о рабочем времени</b>\n\n"
            f"Текущее время выходит за пределы рабочего времени службы доставки (<b>10:00 - 20:00</b>).\n"
            f"{working_hours_msg}\n\n"
            f"Ваш заказ будет принят, но обработка может быть отложена до начала рабочего времени.",
            parse_mode="HTML"
        )
    
    # Get order data from state
    data = await state.get_data()
    user_id = message.from_user.id
    
    # Create new order in the database
    order_id = await create_order(
        shop_id=user_id,
        customer_phone=data['customer_phone'],
        city=data['city'],
        shop_name=data['shop_name'],
        delivery_address=data['delivery_address'],
        payment_amount=data.get('payment_amount', 0)
    )
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>Заказ #{order_id} успешно создан!</b>\n\nИнформация о заказе отправлена администратору. Вы получите уведомление, когда заказ будет назначен курьеру.",
        reply_markup=await get_shop_main_keyboard()
    )
    
    # Notify admins about the new order
    payment_amount = data.get('payment_amount', 0)
    payment_formatted = f"{payment_amount:.2f}" if payment_amount > 0 else "Нет"
    
    order_notification = (
        f"📦 <b>Новый заказ #{order_id}</b>\n\n"
        f"🏪 От магазина: {data['shop_name']}\n"
        f"📱 Телефон клиента: {data['customer_phone']}\n"
        f"🏙️ Город: {data['city']}\n"
        f"📍 Адрес доставки: {data['delivery_address']}\n"
        f"💰 Сумма к оплате: {payment_formatted} сомони"
    )
    
    bot = message.bot
    for admin_id in ADMIN_CHAT_IDS:
        try:
            await bot.send_message(admin_id, order_notification)
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")


@router.message(Command("myorders"))
@router.message(F.text == "📋 Мои заказы")
async def cmd_my_orders(message: Message):
    """Handler for /myorders command to view shop's orders"""
    if not await shop_access_required(message):
        await message.answer("Эта команда доступна только магазинам. Пожалуйста, зарегистрируйтесь как магазин.")
        return
    
    # Информационно уведомляем о нерабочем времени, но позволяем просматривать заказы
    if not is_working_hours():
        working_hours_msg = get_working_hours_message()
        await message.answer(
            f"ℹ️ <b>Информация о рабочем времени</b>\n\n"
            f"Текущее время выходит за пределы рабочего времени службы доставки (<b>10:00 - 20:00</b>).\n"
            f"{working_hours_msg}\n\n"
            f"Обработка новых заказов может быть отложена до начала рабочего времени.",
            parse_mode="HTML"
        )
    
    user_id = message.from_user.id
    orders = await get_shop_orders(user_id)
    
    if not orders:
        await message.answer(
            "У вас еще нет заказов. Используйте кнопку '📦 Новый заказ', чтобы создать новый заказ на доставку.",
            reply_markup=await get_shop_main_keyboard()
        )
        return
    
    # Display all orders for the shop
    response = "📋 <b>Ваши заказы:</b>\n\n"
    for order in orders:
        status = order.get('status', 'pending')
        status_text = {
            'pending': 'Ожидает',
            'assigned': 'Назначен',
            'delivered': 'Доставлен'
        }.get(status, status)
        
        status_emoji = "🟢" if status == "delivered" else "🟡" if status == "assigned" else "🔴"
        
        # Форматируем сумму оплаты
        payment_amount = order.get('payment_amount', 0)
        payment_formatted = f"{payment_amount:.2f}" if payment_amount > 0 else "Нет"
        
        response += (
            f"📦 <b>Заказ #{order['id']}</b> - {status_emoji} {status_text}\n"
            f"📱 Клиент: {order['customer_phone']}\n"
            f"📍 Адрес: {order['city']}, {order['delivery_address']}\n"
            f"💰 Сумма к оплате: {payment_formatted} сомони\n"
        )
        
        if status == "delivered" and "delivered_at" in order:
            response += f"🕒 Доставлен в: {order['delivered_at']}\n"
        
        if status == "assigned" and "courier_name" in order:
            response += f"🚚 Курьер: {order['courier_name']}\n"
            
        response += "\n"
    
    await message.answer(response, reply_markup=await get_shop_main_keyboard())


def register_handlers(dp: Router):
    """Register all shop handlers"""
    dp.include_router(router)