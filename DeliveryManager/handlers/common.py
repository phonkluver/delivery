"""
Common handlers for all users regardless of role.
This module contains handlers for commands available to all users.
"""
import logging
from aiogram import Router, F, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import (
    ROLE_ADMIN, ROLE_SHOP, ROLE_COURIER, ADMIN_CHAT_IDS,
    USE_WHITELIST, WHITELISTED_USERS, add_user_to_whitelist
)
from storage.database import (
    get_user_role, register_user, 
    get_authorized_users, add_authorized_user, init_whitelist
)
from utils.timezone import (
    get_datetime_dushanbe, format_datetime_dushanbe, is_working_hours, get_working_hours_message
)

logger = logging.getLogger(__name__)

# Create a router for common handlers
router = Router()


class AccessVerification(StatesGroup):
    """States for access verification process"""
    waiting_for_access_code = State()


class RoleRegistration(StatesGroup):
    """States for role registration process"""
    waiting_for_role = State()
    waiting_for_courier_name = State()
    waiting_for_courier_phone = State()
    waiting_for_shop_name = State()
    waiting_for_shop_phone = State()


# Список авторизованных пользователей (сохраняется в памяти до перезапуска)
authorized_users = set(ADMIN_CHAT_IDS)  # Администраторы всегда авторизованы


async def check_user_access(user_id: int) -> bool:
    """Проверяет, имеет ли пользователь доступ к боту"""
    # Администраторы всегда имеют доступ
    if user_id in ADMIN_CHAT_IDS:
        return True
    
    # Проверка по белому списку, если включено
    if USE_WHITELIST:
        authorized_users_list = await get_authorized_users()
        return user_id in WHITELISTED_USERS or user_id in authorized_users_list
    
    # Если белый список не используется, все пользователи имеют доступ
    return True


@router.message(CommandStart(), StateFilter("*"))
async def cmd_start(message: Message, state: FSMContext):
    """Handler for /start command"""
    await state.clear()
    user_id = message.from_user.id
    
    # Информационно отображаем о рабочем времени, но не блокируем работу
    if not is_working_hours():
        # Бот продолжает работать, просто информируем о времени работы службы доставки
        logger.info(f"User {user_id} using bot outside of working hours")
    
    
    # Проверяем доступ пользователя по белому списку
    has_access = await check_user_access(user_id)
    
    # Если включен белый список и пользователя нет в нем
    if USE_WHITELIST and not has_access:
        await message.answer(
            "⛔ <b>Доступ запрещен</b>\n\n"
            "Вы не можете использовать этого бота, поскольку ваш ID не находится в списке разрешенных пользователей.\n\n"
            "Пожалуйста, свяжитесь с администратором для получения доступа.",
            parse_mode="HTML"
        )
        # Отправляем уведомление администратору о попытке доступа
        bot = message.bot
        user_username = message.from_user.username or "нет"
        user_name = message.from_user.full_name or "Неизвестно"
        
        for admin_id in ADMIN_CHAT_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    f"⚠️ <b>Попытка доступа от неавторизованного пользователя</b>\n\n"
                    f"👤 <b>Имя:</b> {user_name}\n"
                    f"🆔 <b>ID:</b> {user_id}\n"
                    f"📝 <b>Username:</b> @{user_username}\n\n"
                    f"Чтобы добавить этого пользователя в белый список, используйте команду:\n"
                    f"<code>/whitelist_add {user_id}</code>",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id} about unauthorized access: {e}")
        return
    
    # Если пользователь имеет доступ, проверяем его роль
    role = await get_user_role(user_id)
    
    if role:
        await message.answer(f"✨ Добро пожаловать! Вы зарегистрированы как {role.capitalize()}.")
        
        if role == ROLE_ADMIN:
            kb = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text="📋 Список заказов"), KeyboardButton(text="📮 Назначить заказ")],
                [KeyboardButton(text="👥 Управление пользователями"), KeyboardButton(text="📊 Отчет")],
                [KeyboardButton(text="❓ Помощь")]
            ], resize_keyboard=True)
            await message.answer("🔍 Выберите действие:", reply_markup=kb)
            
        elif role == ROLE_SHOP:
            kb = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text="📦 Новый заказ"), KeyboardButton(text="📋 Мои заказы")],
                [KeyboardButton(text="❓ Помощь")]
            ], resize_keyboard=True)
            await message.answer("🔍 Выберите действие:", reply_markup=kb)
            
        elif role == ROLE_COURIER:
            kb = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text="🚚 Мои доставки")],
                [KeyboardButton(text="❓ Помощь")]
            ], resize_keyboard=True)
            await message.answer("🔍 Выберите действие:", reply_markup=kb)
    else:
        register_kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🔐 Зарегистрироваться")]
        ], resize_keyboard=True)
        
        await message.answer(
            "🌟 Добро пожаловать в TUKTUK - КУРЬЕРСКАЯ СЛУЖБА | ДОСТАВКА! 🌟\n\n"
            "🛵 Служба доставки для Интернет-магазинов\n"
            "🚀 Быстро, легко, надёжно и удобно\n"
            "🕗 График работы от 10:00 до 20:00\n\n"
            "💼 Этот бот помогает координировать доставки между магазинами, администраторами и курьерами.\n\n"
            "🔐 Пожалуйста, нажмите кнопку \"Зарегистрироваться\" чтобы выбрать вашу роль.",
            reply_markup=register_kb
        )


@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message):
    """Handler for /help command or Help button"""
    user_id = message.from_user.id
    role = await get_user_role(user_id)
    
    if not role:
        await message.answer(
            "ℹ️ <b>Добро пожаловать в службу помощи TUKTUK!</b>\n\n"
            "🔐 Сначала вам нужно зарегистрироваться. Нажмите кнопку \"🔐 Зарегистрироваться\".\n\n"
            "<b>Доступные роли:</b>\n"
            "🛒 <b>Магазин</b>: Создавайте заказы на доставку\n"
            "⚙️ <b>Администратор</b>: Управляйте заказами и назначайте курьеров\n"
            "🚚 <b>Курьер</b>: Доставляйте заказы и отмечайте их как выполненные\n\n"
            "⏰ <b>График работы:</b> 10:00 - 20:00"
        )
        return
    
    if role == ROLE_SHOP:
        help_text = (
            "📱 <b>TUKTUK - СЛУЖБА ДОСТАВКИ</b>\n\n"
            "🛒 <b>Функции для магазина:</b>\n\n"
            "📦 <b>Новый заказ</b> - Создать новый заказ на доставку\n"
            "📋 <b>Мои заказы</b> - Просмотреть ваши текущие заказы\n"
            "❌ <b>Отмена</b> - Отменить текущую операцию\n\n"
            "⏰ <b>График работы:</b> 10:00 - 20:00\n"
            "📞 <b>Поддержка:</b> Свяжитесь с администратором для помощи"
        )
    elif role == ROLE_ADMIN:
        help_text = (
            "📱 <b>TUKTUK - СЛУЖБА ДОСТАВКИ</b>\n\n"
            "⚙️ <b>Функции для администратора:</b>\n\n"
            "📋 <b>Список заказов</b> - Просмотреть все ожидающие заказы\n"
            "📮 <b>Назначить заказ</b> - Назначить заказ курьеру\n"
            "👥 <b>Управление пользователями</b> - Управление белым списком\n"
            "📊 <b>Отчет</b> - Сформировать отчет о доставках\n"
            "❌ <b>Отмена</b> - Отменить текущую операцию\n\n"
            "<b>Команды белого списка:</b>\n"
            "/whitelist_add [ID] - Добавить пользователя в белый список\n"
            "/whitelist_list - Показать пользователей в белом списке\n"
            "/whitelist_remove [ID] - Удалить пользователя из белого списка\n\n"
            "<b>Экспорт в Excel:</b>\n"
            "/export_orders - Экспортировать все заказы в Excel файл\n\n"
            "⏰ <b>График работы:</b> 10:00 - 20:00"
        )
    elif role == ROLE_COURIER:
        help_text = (
            "📱 <b>TUKTUK - СЛУЖБА ДОСТАВКИ</b>\n\n"
            "🚚 <b>Функции для курьера:</b>\n\n"
            "🚚 <b>Мои доставки</b> - Просмотреть назначенные вам доставки\n"
            "❌ <b>Отмена</b> - Отменить текущую операцию\n\n"
            "🔔 Вы получите уведомление, когда вам будет назначена доставка.\n\n"
            "⏰ <b>График работы:</b> 10:00 - 20:00\n"
            "📞 <b>Поддержка:</b> Свяжитесь с администратором для помощи"
        )
    else:
        help_text = "⚠️ Неизвестная роль. Пожалуйста, свяжитесь с администратором."
    
    await message.answer(help_text)


@router.message(Command("register"))
@router.message(Command("resetrole"))
@router.message(F.text == "🔐 Зарегистрироваться")
@router.message(F.text == "🔄 Сбросить роль")
async def cmd_register(message: Message, state: FSMContext):
    """Handler for register command or button to set user role"""
    await state.clear()
    user_id = message.from_user.id
    
    # Информационно уведомляем о нерабочем времени, но позволяем регистрироваться
    if not is_working_hours():
        working_hours_msg = get_working_hours_message()
        await message.answer(
            f"ℹ️ <b>Информация о рабочем времени</b>\n\n"
            f"Текущее время выходит за пределы рабочего времени службы доставки (<b>10:00 - 20:00</b>).\n"
            f"{working_hours_msg}\n\n"
            f"Регистрация будет выполнена, но обработка заказов может быть отложена до начала рабочего времени.",
            parse_mode="HTML"
        )
    
    # Check if user already has a role
    role = await get_user_role(user_id)
    is_reset = message.text == "/resetrole" or message.text == "🔄 Сбросить роль"
    
    if role and not is_reset:
        reset_kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🔄 Сбросить роль")]
        ], resize_keyboard=True)
        await message.answer(
            f"Вы уже зарегистрированы как {role.capitalize()}.\n"
            "Если вы хотите изменить свою роль, используйте команду /resetrole или нажмите кнопку ниже.",
            reply_markup=reset_kb
        )
        return
    
    # For admin role, check if user ID is in the allowed admin list
    if user_id in ADMIN_CHAT_IDS:
        roles_kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🛒 Магазин"), KeyboardButton(text="⚙️ Администратор"), KeyboardButton(text="🚚 Курьер")]
        ], resize_keyboard=True)
    else:
        roles_kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🛒 Магазин"), KeyboardButton(text="🚚 Курьер")]
        ], resize_keyboard=True)
    
    await message.answer("🔍 Пожалуйста, выберите вашу роль:", reply_markup=roles_kb)
    await state.set_state(RoleRegistration.waiting_for_role)


@router.message(RoleRegistration.waiting_for_role)
async def process_role_selection(message: Message, state: FSMContext):
    """Process the selected role"""
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    # Extract role from button text
    text = message.text.lower()
    if "магазин" in text or "shop" in text:
        selected_role = ROLE_SHOP
    elif "администратор" in text or "admin" in text:
        selected_role = ROLE_ADMIN
    elif "курьер" in text or "courier" in text:
        selected_role = ROLE_COURIER
    else:
        selected_role = None
    
    if selected_role not in [ROLE_ADMIN, ROLE_SHOP, ROLE_COURIER]:
        await message.answer(
            "❌ <b>Ошибка:</b> Пожалуйста, выберите правильную роль, используя кнопки.",
            parse_mode="HTML"
        )
        return
    
    # Only allow admin registration for users in the admin list
    if selected_role == ROLE_ADMIN and user_id not in ADMIN_CHAT_IDS:
        await message.answer(
            "⛔ <b>Ошибка доступа:</b> У вас нет прав для регистрации в качестве администратора. "
            "Пожалуйста, выберите другую роль.",
            parse_mode="HTML"
        )
        return
    
    # Сохраняем выбранную роль в состояние
    await state.update_data(selected_role=selected_role)
    
    cancel_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
    
    # Если выбрана роль курьера, запросим его имя
    if selected_role == ROLE_COURIER:
        await message.answer(
            "🧑‍💼 <b>Регистрация курьера</b>\n\n"
            "Пожалуйста, введите ваше <b>полное имя</b>.\n\n"
            "⚠️ Это имя будет отображаться клиентам и администратору при доставке заказов.",
            reply_markup=cancel_kb,
            parse_mode="HTML"
        )
        await state.set_state(RoleRegistration.waiting_for_courier_name)
        return
    
    # Если выбрана роль магазина, запросим название магазина
    if selected_role == ROLE_SHOP:
        await message.answer(
            "🏪 <b>Регистрация магазина</b>\n\n"
            "Пожалуйста, введите <b>название вашего магазина</b>.\n\n"
            "⚠️ Это название будет отображаться в заказах на доставку.",
            reply_markup=cancel_kb,
            parse_mode="HTML"
        )
        await state.set_state(RoleRegistration.waiting_for_shop_name)
        return
    
    # Для роли админа сразу регистрируем пользователя
    await register_user(
        user_id=user_id,
        username=user_name,
        role=selected_role
    )
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>Вы успешно зарегистрированы как ⚙️ Администратор!</b>",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    
    # Предоставляем инструкции для администратора
    admin_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📋 Список заказов"), KeyboardButton(text="📮 Назначить заказ")],
        [KeyboardButton(text="👥 Управление пользователями"), KeyboardButton(text="📊 Отчет")],
        [KeyboardButton(text="❓ Помощь")]
    ], resize_keyboard=True)
    
    await message.answer(
        "📋 Чтобы просмотреть все ожидающие заказы, нажмите кнопку <b>\"📋 Список заказов\"</b>", 
        reply_markup=admin_kb,
        parse_mode="HTML"
    )


@router.message(RoleRegistration.waiting_for_shop_name)
async def process_shop_name(message: Message, state: FSMContext):
    """Process shop name input"""
    shop_name = message.text.strip()
    
    # Минимальная проверка названия магазина
    if len(shop_name) < 2:
        await message.answer(
            "❌ <b>Ошибка:</b> Название магазина слишком короткое.\n\n"
            "Пожалуйста, введите корректное название магазина.",
            parse_mode="HTML"
        )
        return
    
    # Сохраняем название магазина
    await state.update_data(shop_name=shop_name)
    
    # Запрашиваем номер телефона магазина
    cancel_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
    
    await message.answer(
        "📱 <b>Регистрация магазина</b>\n\n"
        "Пожалуйста, введите <b>контактный номер телефона</b> вашего магазина.\n\n"
        "⚠️ Этот номер будет использоваться для связи по вопросам доставки.",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )
    await state.set_state(RoleRegistration.waiting_for_shop_phone)


@router.message(RoleRegistration.waiting_for_shop_phone)
async def process_shop_phone(message: Message, state: FSMContext):
    """Process shop phone input"""
    shop_phone = message.text.strip()
    
    # Простая проверка номера телефона 
    if len(shop_phone) < 5:
        await message.answer(
            "❌ <b>Ошибка:</b> Введен некорректный номер телефона.\n\n"
            "Пожалуйста, введите действительный номер телефона.",
            parse_mode="HTML"
        )
        return
    
    # Получаем данные из состояния
    data = await state.get_data()
    selected_role = data.get('selected_role')
    shop_name = data.get('shop_name')
    
    if not selected_role or selected_role != ROLE_SHOP or not shop_name:
        await message.answer(
            "❌ <b>Ошибка:</b> Произошла ошибка при обработке данных.\n\n"
            "Пожалуйста, начните регистрацию заново.",
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    user_id = message.from_user.id
    
    # Формируем полное имя магазина с номером телефона
    full_shop_info = f"{shop_name} | {shop_phone}"
    
    # Регистрируем магазин
    await register_user(
        user_id=user_id,
        username=full_shop_info,  # Сохраняем название магазина и телефон
        role=selected_role
    )
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>Вы успешно зарегистрированы как 🛒 Магазин!</b>\n\n"
        f"🏪 <b>Название магазина:</b> {shop_name}\n"
        f"📱 <b>Контактный телефон:</b> {shop_phone}",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    
    # Предоставляем инструкции для магазина
    shop_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📦 Новый заказ"), KeyboardButton(text="📋 Мои заказы")],
        [KeyboardButton(text="❓ Помощь")]
    ], resize_keyboard=True)
    
    await message.answer(
        "📝 Чтобы создать новый заказ на доставку, нажмите кнопку <b>\"📦 Новый заказ\"</b>", 
        reply_markup=shop_kb,
        parse_mode="HTML"
    )
    
    # Отправляем уведомление администратору о регистрации нового магазина
    bot = message.bot
    for admin_id in ADMIN_CHAT_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🏪 <b>Зарегистрирован новый магазин!</b>\n\n"
                f"🛒 <b>Название магазина:</b> {shop_name}\n"
                f"📱 <b>Контактный телефон:</b> {shop_phone}\n"
                f"🆔 <b>ID:</b> {user_id}",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id} about new shop: {e}")


@router.message(RoleRegistration.waiting_for_courier_name)
async def process_courier_name(message: Message, state: FSMContext):
    """Process courier name input"""
    courier_name = message.text.strip()
    
    # Минимальная проверка имени курьера
    if len(courier_name) < 2:
        await message.answer(
            "❌ <b>Ошибка:</b> Имя слишком короткое.\n\n"
            "Пожалуйста, введите ваше полное имя.",
            parse_mode="HTML"
        )
        return
    
    # Сохраняем имя курьера в состоянии
    await state.update_data(courier_name=courier_name)
    
    # Запрашиваем номер телефона курьера
    cancel_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
    
    await message.answer(
        "📱 <b>Регистрация курьера</b>\n\n"
        "Пожалуйста, введите <b>ваш контактный номер телефона</b>.\n\n"
        "⚠️ Этот номер будет отображаться администраторам для коммуникации.",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )
    await state.set_state(RoleRegistration.waiting_for_courier_phone)


@router.message(RoleRegistration.waiting_for_courier_phone)
async def process_courier_phone(message: Message, state: FSMContext):
    """Process courier phone input"""
    courier_phone = message.text.strip()
    
    # Простая проверка номера телефона 
    if len(courier_phone) < 5:
        await message.answer(
            "❌ <b>Ошибка:</b> Введен некорректный номер телефона.\n\n"
            "Пожалуйста, введите действительный номер телефона.",
            parse_mode="HTML"
        )
        return
    
    # Получаем данные из состояния
    data = await state.get_data()
    selected_role = data.get('selected_role')
    courier_name = data.get('courier_name')
    
    if not selected_role or selected_role != ROLE_COURIER or not courier_name:
        await message.answer(
            "❌ <b>Ошибка:</b> Произошла ошибка при обработке данных.\n\n"
            "Пожалуйста, начните регистрацию заново.",
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    user_id = message.from_user.id
    
    # Формируем полное имя курьера с номером телефона для сохранения в БД
    full_courier_info = f"{courier_name} | {courier_phone}"
    
    # Регистрируем курьера
    await register_user(
        user_id=user_id,
        username=full_courier_info,  # Сохраняем имя и телефон
        role=selected_role
    )
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>Вы успешно зарегистрированы как 🚚 Курьер!</b>\n\n"
        f"👤 <b>Ваше имя в системе:</b> {courier_name}\n"
        f"📱 <b>Контактный телефон:</b> {courier_phone}",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    
    # Предоставляем инструкции для курьера
    courier_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚚 Мои доставки")],
        [KeyboardButton(text="❓ Помощь")]
    ], resize_keyboard=True)
    
    await message.answer(
        "🔔 Вы получите уведомление, когда вам будет назначена доставка.",
        reply_markup=courier_kb,
        parse_mode="HTML"
    )
    
    # Отправляем уведомление администратору о регистрации нового курьера
    bot = message.bot
    for admin_id in ADMIN_CHAT_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🆕 <b>Зарегистрирован новый курьер!</b>\n\n"
                f"👤 <b>Имя:</b> {courier_name}\n"
                f"📱 <b>Телефон:</b> {courier_phone}\n"
                f"🆔 <b>ID:</b> {user_id}",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id} about new courier: {e}")


@router.message(Command("cancel"), StateFilter("*"))
@router.message(F.text == "❌ Отмена", StateFilter("*"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Handler for /cancel command to cancel current operation"""
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer(
            "❌ Текущая операция отменена.",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Restore appropriate keyboard based on user role
        user_id = message.from_user.id
        role = await get_user_role(user_id)
        
        if role == ROLE_SHOP:
            shop_kb = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text="📦 Новый заказ"), KeyboardButton(text="📋 Мои заказы")],
                [KeyboardButton(text="❓ Помощь")]
            ], resize_keyboard=True)
            await message.answer("Вернулись в главное меню магазина", reply_markup=shop_kb)
        elif role == ROLE_ADMIN:
            admin_kb = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text="📋 Список заказов"), KeyboardButton(text="📮 Назначить заказ")],
                [KeyboardButton(text="👥 Управление пользователями"), KeyboardButton(text="📊 Отчет")],
                [KeyboardButton(text="❓ Помощь")]
            ], resize_keyboard=True)
            await message.answer("Вернулись в главное меню администратора", reply_markup=admin_kb)
        elif role == ROLE_COURIER:
            courier_kb = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text="🚚 Мои доставки")],
                [KeyboardButton(text="❓ Помощь")]
            ], resize_keyboard=True)
            await message.answer("Вернулись в главное меню курьера", reply_markup=courier_kb)
    else:
        await message.answer("❕ Нет активных операций для отмены.")


# Обработчики команд управления белым списком
@router.message(Command('whitelist_add'))
async def cmd_whitelist_add(message: Message):
    """Добавление пользователя в белый список (только для админов)"""
    user_id = message.from_user.id
    
    # Проверяем, что команду выполняет администратор
    if user_id not in ADMIN_CHAT_IDS:
        await message.answer("⛔ Эта команда доступна только администраторам.")
        return
    
    # Извлекаем ID пользователя из сообщения
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ <b>Ошибка:</b> Не указан ID пользователя.\n\n"
            "Используйте формат: <code>/whitelist_add USER_ID</code>",
            parse_mode="HTML"
        )
        return
    
    try:
        target_user_id = int(args[1].strip())
        success = await add_authorized_user(target_user_id)
        
        if success:
            await message.answer(
                f"✅ <b>Пользователь с ID {target_user_id} успешно добавлен в белый список.</b>",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"❌ <b>Ошибка при добавлении пользователя в белый список.</b>",
                parse_mode="HTML"
            )
    except ValueError:
        await message.answer(
            "❌ <b>Ошибка:</b> ID пользователя должен быть числом.\n\n"
            "Используйте формат: <code>/whitelist_add USER_ID</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in whitelist_add command: {e}")
        await message.answer(
            f"❌ <b>Произошла ошибка:</b> {str(e)}",
            parse_mode="HTML"
        )


@router.message(Command('whitelist_list'))
async def cmd_whitelist_list(message: Message):
    """Просмотр списка пользователей в белом списке (только для админов)"""
    user_id = message.from_user.id
    
    # Проверяем, что команду выполняет администратор
    if user_id not in ADMIN_CHAT_IDS:
        await message.answer("⛔ Эта команда доступна только администраторам.")
        return
    
    try:
        # Получаем список авторизованных пользователей
        authorized_users_list = await get_authorized_users()
        
        if not authorized_users_list:
            await message.answer(
                "📋 <b>Белый список пользователей пуст.</b>",
                parse_mode="HTML"
            )
            return
        
        # Формируем сообщение со списком пользователей
        users_text = "\n".join([f"• {user_id}" for user_id in authorized_users_list])
        
        await message.answer(
            f"📋 <b>Пользователи в белом списке:</b>\n\n{users_text}",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in whitelist_list command: {e}")
        await message.answer(
            f"❌ <b>Произошла ошибка:</b> {str(e)}",
            parse_mode="HTML"
        )


@router.message(Command('whitelist_remove'))
async def cmd_whitelist_remove(message: Message):
    """Удаление пользователя из белого списка (только для админов)"""
    user_id = message.from_user.id
    
    # Проверяем, что команду выполняет администратор
    if user_id not in ADMIN_CHAT_IDS:
        await message.answer("⛔ Эта команда доступна только администраторам.")
        return
    
    # Извлекаем ID пользователя из сообщения
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ <b>Ошибка:</b> Не указан ID пользователя.\n\n"
            "Используйте формат: <code>/whitelist_remove USER_ID</code>",
            parse_mode="HTML"
        )
        return
    
    try:
        target_user_id = int(args[1].strip())
        
        # Не даем удалить админа из белого списка
        if target_user_id in ADMIN_CHAT_IDS:
            await message.answer(
                "⛔ <b>Нельзя удалить администратора из белого списка.</b>",
                parse_mode="HTML"
            )
            return
        
        # Удаляем пользователя из белого списка
        from storage.database import remove_authorized_user
        success = await remove_authorized_user(target_user_id)
        
        if success:
            await message.answer(
                f"✅ <b>Пользователь с ID {target_user_id} успешно удален из белого списка.</b>",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"❌ <b>Пользователь с ID {target_user_id} не найден в белом списке.</b>",
                parse_mode="HTML"
            )
    except ValueError:
        await message.answer(
            "❌ <b>Ошибка:</b> ID пользователя должен быть числом.\n\n"
            "Используйте формат: <code>/whitelist_remove USER_ID</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in whitelist_remove command: {e}")
        await message.answer(
            f"❌ <b>Произошла ошибка:</b> {str(e)}",
            parse_mode="HTML"
        )


@router.message(Command('export_orders'))
async def cmd_export_orders(message: Message):
    """Экспорт заказов в Excel файл (только для админов)"""
    user_id = message.from_user.id
    
    # Проверяем, что команду выполняет администратор
    if user_id not in ADMIN_CHAT_IDS:
        await message.answer("⛔ Эта команда доступна только администраторам.")
        return
    
    try:
        # Получаем все заказы из базы данных
        from storage.database import get_all_orders, export_orders_to_excel
        orders = await get_all_orders()
        
        if not orders:
            await message.answer(
                "📊 <b>Нет заказов для экспорта</b>",
                parse_mode="HTML"
            )
            return
        
        # Уведомляем о начале экспорта
        await message.answer(
            "⏳ <b>Генерация отчета...</b>",
            parse_mode="HTML"
        )
        
        # Экспортируем заказы в Excel
        filepath = await export_orders_to_excel(orders)
        
        # Отправляем файл
        await message.bot.send_document(
            chat_id=message.chat.id,
            document=types.FSInputFile(filepath),
            caption="📊 <b>Отчет о заказах</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in export_orders command: {e}")
        await message.answer(
            f"❌ <b>Произошла ошибка при экспорте заказов:</b> {str(e)}",
            parse_mode="HTML"
        )


@router.message(F.text == "👥 Управление пользователями")
async def cmd_user_management(message: Message):
    """Обработчик для кнопки 'Управление пользователями'"""
    user_id = message.from_user.id
    
    # Проверяем, что команду выполняет администратор
    if user_id not in ADMIN_CHAT_IDS:
        await message.answer("⛔ Эта команда доступна только администраторам.")
        return
    
    # Создаем клавиатуру для управления пользователями
    user_management_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🔍 Просмотреть белый список"), KeyboardButton(text="✅ Добавить в белый список")],
        [KeyboardButton(text="❌ Удалить из белого списка"), KeyboardButton(text="🔙 Назад")]
    ], resize_keyboard=True)
    
    await message.answer(
        "👥 <b>Управление пользователями</b>\n\n"
        "Выберите действие:",
        reply_markup=user_management_kb,
        parse_mode="HTML"
    )


@router.message(F.text == "🔙 Назад")
async def cmd_back_to_main_menu_admin(message: Message):
    """Возврат в главное меню для админа"""
    user_id = message.from_user.id
    role = await get_user_role(user_id)
    
    if role == ROLE_ADMIN:
        admin_kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="📋 Список заказов"), KeyboardButton(text="📮 Назначить заказ")],
            [KeyboardButton(text="👥 Управление пользователями"), KeyboardButton(text="📊 Отчет")],
            [KeyboardButton(text="❓ Помощь")]
        ], resize_keyboard=True)
        
        await message.answer(
            "🔍 Выберите действие:",
            reply_markup=admin_kb
        )


@router.message(F.text == "🔍 Просмотреть белый список")
async def cmd_view_whitelist(message: Message):
    """Обработчик для просмотра белого списка"""
    await cmd_whitelist_list(message)


@router.message(F.text == "✅ Добавить в белый список")
async def cmd_add_to_whitelist_start(message: Message):
    """Начало процесса добавления в белый список"""
    user_id = message.from_user.id
    
    if user_id not in ADMIN_CHAT_IDS:
        await message.answer("⛔ Эта функция доступна только администраторам.")
        return
    
    await message.answer(
        "✅ <b>Добавление пользователя в белый список</b>\n\n"
        "Введите ID пользователя, которого хотите добавить, или перешлите сообщение от этого пользователя.\n\n"
        "Для отмены нажмите <b>🔙 Назад</b>",
        parse_mode="HTML"
    )


@router.message(F.text == "❌ Удалить из белого списка")
async def cmd_remove_from_whitelist_start(message: Message):
    """Начало процесса удаления из белого списка"""
    user_id = message.from_user.id
    
    if user_id not in ADMIN_CHAT_IDS:
        await message.answer("⛔ Эта функция доступна только администраторам.")
        return
    
    await message.answer(
        "❌ <b>Удаление пользователя из белого списка</b>\n\n"
        "Введите ID пользователя, которого хотите удалить из белого списка.\n\n"
        "Для отмены нажмите <b>🔙 Назад</b>",
        parse_mode="HTML"
    )


def register_handlers(dp: Router):
    """Register all common handlers"""
    dp.include_router(router)
