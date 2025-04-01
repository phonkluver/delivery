"""
Handlers for admin users.
This module contains handlers for admin-specific commands and functions.
"""
import logging
import re
from utils.timezone import get_date_dushanbe, get_yesterday_date
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ROLE_ADMIN, ADMIN_CHAT_IDS
from keyboards.admin_kb import (
    get_admin_main_keyboard, get_couriers_keyboard,
    get_courier_management_keyboard, get_shop_management_keyboard,
    get_couriers_list_keyboard, get_shops_list_keyboard
)
from storage.database import (
    get_user_role, get_pending_orders, get_order_by_id, 
    assign_order_to_courier, get_couriers, get_all_orders,
    get_delivered_orders_in_timeframe, get_all_shops, get_all_couriers,
    delete_user, check_user_has_orders
)

logger = logging.getLogger(__name__)

# Create a router for admin handlers
router = Router()


class AssignOrderForm(StatesGroup):
    """States for order assignment process"""
    waiting_for_order_id = State()
    waiting_for_courier = State()


class UserManagementForm(StatesGroup):
    """States for user management process"""
    waiting_for_courier_deletion = State()
    waiting_for_shop_deletion = State()
    confirm_deletion = State()


async def admin_access_required(message: Message):
    """Check if user has admin role"""
    user_id = message.from_user.id
    role = await get_user_role(user_id)
    return role == ROLE_ADMIN


@router.message(Command("orders"))
@router.message(F.text == "📋 Список заказов")
async def cmd_view_orders(message: Message):
    """Handler for /orders command to view all pending orders"""
    if not await admin_access_required(message):
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    orders = await get_pending_orders()
    
    if not orders:
        await message.answer(
            "На данный момент нет заказов в ожидании.",
            reply_markup=await get_admin_main_keyboard()
        )
        return
    
    response = "📋 <b>Заказы в ожидании:</b>\n\n"
    for order in orders:
        # Форматируем сумму оплаты
        payment_amount = order.get('payment_amount', 0)
        payment_formatted = f"{payment_amount:.2f}" if payment_amount > 0 else "Нет"
        
        response += (
            f"Заказ <b>#{order['id']}</b>\n"
            f"🏪 Магазин: {order['shop_name']}\n"
            f"📱 Клиент: {order['customer_phone']}\n"
            f"📍 Адрес: {order['city']}, {order['delivery_address']}\n"
            f"💰 Сумма к оплате: {payment_formatted} сомони\n"
            f"🔄 Статус: {order['status'].capitalize()}\n\n"
        )
    
    response += "Используйте кнопку '📮 Назначить заказ' чтобы назначить заказ курьеру."
    await message.answer(response, reply_markup=await get_admin_main_keyboard())


@router.message(Command("assign"), StateFilter("*"))
@router.message(F.text == "📮 Назначить заказ", StateFilter("*"))
async def cmd_assign_order(message: Message, state: FSMContext):
    """Handler for /assign command to assign an order to a courier"""
    if not await admin_access_required(message):
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    await state.clear()
    
    # Get pending orders
    orders = await get_pending_orders()
    
    if not orders:
        await message.answer(
            "Нет заказов для назначения.",
            reply_markup=await get_admin_main_keyboard()
        )
        return
    
    # Display orders for selection
    response = "Выберите заказ для назначения, отправив его номер (ID):\n\n"
    for order in orders:
        # Форматируем сумму оплаты
        payment_amount = order.get('payment_amount', 0)
        payment_formatted = f"{payment_amount:.2f}" if payment_amount > 0 else "Нет"
        
        response += (
            f"Заказ <b>#{order['id']}</b>\n"
            f"🏪 Магазин: {order['shop_name']}\n"
            f"📱 Клиент: {order['customer_phone']}\n"
            f"📍 Адрес: {order['city']}, {order['delivery_address']}\n"
            f"💰 Сумма к оплате: {payment_formatted} сомони\n\n"
        )
    
    await message.answer(response)
    await state.set_state(AssignOrderForm.waiting_for_order_id)


@router.message(AssignOrderForm.waiting_for_order_id)
async def process_order_id_selection(message: Message, state: FSMContext):
    """Process order ID selection for assignment"""
    # Обработка отмены операции
    if message.text.lower() in ["отмена", "cancel", "отменить"]:
        await message.answer(
            "Операция назначения заказа отменена.",
            reply_markup=await get_admin_main_keyboard()
        )
        await state.clear()
        return
    
    try:
        order_id = int(message.text)
        order = await get_order_by_id(order_id)
        
        if not order:
            await message.answer(
                "Заказ не найден. Пожалуйста, введите правильный номер заказа или отправьте 'отмена' для возврата в меню."
            )
            return
        
        if order['status'] != 'pending':
            await message.answer(
                f"Заказ #{order_id} уже {order['status']}. Пожалуйста, выберите заказ в статусе ожидания или отправьте 'отмена'."
            )
            return
        
        # Save order ID in state
        await state.update_data(order_id=order_id)
        
        # Get couriers for selection
        couriers = await get_couriers()
        
        if not couriers:
            await message.answer(
                "Нет зарегистрированных курьеров. Пожалуйста, попросите курьеров зарегистрироваться.",
                reply_markup=await get_admin_main_keyboard()
            )
            await state.clear()
            return
        
        # Display order details and courier selection keyboard
        courier_kb = await get_couriers_keyboard(couriers)
        
        # Форматируем сумму оплаты
        payment_amount = order.get('payment_amount', 0)
        payment_formatted = f"{payment_amount:.2f}" if payment_amount > 0 else "Нет"
        
        await message.answer(
            f"<b>Назначение заказа #{order_id}</b>\n\n"
            f"🏪 Магазин: {order['shop_name']}\n"
            f"📱 Клиент: {order['customer_phone']}\n"
            f"📍 Адрес: {order['city']}, {order['delivery_address']}\n"
            f"💰 Сумма к оплате: {payment_formatted} сомони\n\n"
            "Выберите курьера:",
            reply_markup=courier_kb
        )
        
        await state.set_state(AssignOrderForm.waiting_for_courier)
        
    except ValueError:
        await message.answer("Пожалуйста, введите корректный номер заказа (только цифры).")


@router.message(AssignOrderForm.waiting_for_courier)
async def process_courier_selection(message: Message, state: FSMContext):
    """Process courier selection for order assignment"""
    # Check if the user wants to cancel
    if message.text == "❌ Отмена":
        await message.answer(
            "Операция отменена.",
            reply_markup=await get_admin_main_keyboard()
        )
        await state.clear()
        return
    
    courier_data = message.text.split(": ")
    
    if len(courier_data) != 2:
        await message.answer("Пожалуйста, выберите курьера из списка.")
        return
    
    courier_name = courier_data[0]
    courier_id = int(courier_data[1])
    
    # Get order ID from state
    data = await state.get_data()
    order_id = data.get('order_id')
    
    # Get order details
    order = await get_order_by_id(order_id)
    
    if not order:
        await message.answer(
            "Заказ не найден. Операция отменена.",
            reply_markup=await get_admin_main_keyboard()
        )
        await state.clear()
        return
    
    # Assign order to courier
    success = await assign_order_to_courier(order_id, courier_id, courier_name)
    
    if not success:
        await message.answer(
            "Не удалось назначить заказ. Пожалуйста, попробуйте еще раз.",
            reply_markup=await get_admin_main_keyboard()
        )
        await state.clear()
        return
    
    await message.answer(
        f"Заказ #{order_id} назначен курьеру {courier_name}.",
        reply_markup=await get_admin_main_keyboard()
    )
    
    # Notify courier about the new assignment
    bot = message.bot
    
    # Форматируем сумму оплаты для уведомления
    payment_amount = order.get('payment_amount', 0)
    payment_formatted = f"{payment_amount:.2f}" if payment_amount > 0 else "Нет"
    
    courier_notification = (
        f"📦 <b>Новое назначение доставки - Заказ #{order_id}</b>\n\n"
        f"📱 Телефон клиента: {order['customer_phone']}\n"
        f"🏙️ Город: {order['city']}\n"
        f"🏪 Магазин: {order['shop_name']}\n"
        f"📍 Адрес доставки: {order['delivery_address']}\n"
        f"💰 Сумма к оплате: {payment_formatted} сомони"
    )
    
    try:
        # Send notification to courier with delivery details and buttons
        from keyboards.courier_kb import get_delivery_confirmation_keyboard
        await bot.send_message(
            courier_id,
            courier_notification,
            reply_markup=await get_delivery_confirmation_keyboard(order_id),
            parse_mode="HTML"
        )
        logger.info(f"Telegram notification sent to courier {courier_id}")
    except Exception as e:
        logger.error(f"Failed to notify courier {courier_id}: {e}")
        await message.answer(f"Предупреждение: Не удалось уведомить курьера о назначении.")
    
    await state.clear()


@router.message(Command("couriers"))
async def cmd_view_couriers(message: Message):
    """Handler for /couriers command to view all registered couriers"""
    if not await admin_access_required(message):
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    couriers = await get_couriers()
    
    if not couriers:
        await message.answer(
            "Пока нет зарегистрированных курьеров.",
            reply_markup=await get_admin_main_keyboard()
        )
        return
    
    response = "📋 <b>Зарегистрированные курьеры:</b>\n\n"
    for courier in couriers:
        # Разделяем имя и телефон курьера (формат: "Имя | Телефон")
        courier_info = courier['username'].split(" | ")
        courier_name = courier_info[0] if len(courier_info) > 0 else "Неизвестно"
        courier_phone = courier_info[1] if len(courier_info) > 1 else "Нет телефона"
        
        response += f"• <b>{courier_name}</b>\n  📱 Телефон: {courier_phone}\n  🆔 ID: {courier['id']}\n\n"
    
    await message.answer(response, reply_markup=await get_admin_main_keyboard(), parse_mode="HTML")


@router.message(F.text == "👥 Управление пользователями")
async def cmd_user_management_redirect(message: Message):
    """Redirect to common handler for user management"""
    if not await admin_access_required(message):
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    # Редирект на обработчик в common.py
    from handlers.common import cmd_user_management
    await cmd_user_management(message)

@router.message(F.text == "👥 Управление курьерами")
async def cmd_courier_management(message: Message):
    """Handler for courier management"""
    if not await admin_access_required(message):
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    await message.answer(
        "Управление курьерами. Выберите действие:",
        reply_markup=await get_courier_management_keyboard()
    )


@router.message(F.text == "🏪 Управление магазинами")
async def cmd_shop_management(message: Message):
    """Handler for shop management"""
    if not await admin_access_required(message):
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    await message.answer(
        "Управление магазинами. Выберите действие:",
        reply_markup=await get_shop_management_keyboard()
    )


@router.message(F.text == "⬅️ Назад в главное меню")
async def cmd_back_to_main_menu(message: Message, state: FSMContext):
    """Handler to return to main menu"""
    if not await admin_access_required(message):
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    await state.clear()
    await message.answer(
        "Вернулись в главное меню администратора.",
        reply_markup=await get_admin_main_keyboard()
    )


@router.message(F.text == "📋 Список курьеров")
async def cmd_list_couriers(message: Message):
    """Handler to list all couriers"""
    if not await admin_access_required(message):
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    couriers = await get_all_couriers()
    
    if not couriers:
        await message.answer(
            "Пока нет зарегистрированных курьеров.",
            reply_markup=await get_courier_management_keyboard()
        )
        return
    
    response = "📋 <b>Зарегистрированные курьеры:</b>\n\n"
    for courier in couriers:
        # Разделяем имя и телефон курьера (формат: "Имя | Телефон")
        courier_info = courier['username'].split(" | ")
        courier_name = courier_info[0] if len(courier_info) > 0 else "Неизвестно"
        courier_phone = courier_info[1] if len(courier_info) > 1 else "Нет телефона"
        
        response += f"• <b>{courier_name}</b>\n  📱 Телефон: {courier_phone}\n  🆔 ID: {courier['id']}\n\n"
    
    await message.answer(response, reply_markup=await get_courier_management_keyboard(), parse_mode="HTML")


@router.message(F.text == "📋 Список магазинов")
async def cmd_list_shops(message: Message):
    """Handler to list all shops"""
    if not await admin_access_required(message):
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    shops = await get_all_shops()
    
    if not shops:
        await message.answer(
            "Пока нет зарегистрированных магазинов.",
            reply_markup=await get_shop_management_keyboard()
        )
        return
    
    response = "📋 <b>Зарегистрированные магазины:</b>\n\n"
    for shop in shops:
        # Разделяем название и телефон магазина (формат: "Название | Телефон")
        shop_info = shop['username'].split(" | ")
        shop_name = shop_info[0] if len(shop_info) > 0 else "Неизвестно"
        shop_phone = shop_info[1] if len(shop_info) > 1 else "Нет телефона"
        
        response += f"• <b>{shop_name}</b>\n  📱 Телефон: {shop_phone}\n  🆔 ID: {shop['id']}\n\n"
    
    await message.answer(response, reply_markup=await get_shop_management_keyboard(), parse_mode="HTML")


@router.message(F.text == "🗑️ Удалить курьера", StateFilter(None))
async def cmd_delete_courier_start(message: Message, state: FSMContext):
    """Handler to start courier deletion process"""
    if not await admin_access_required(message):
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    couriers = await get_all_couriers()
    
    if not couriers:
        await message.answer(
            "Нет курьеров для удаления.",
            reply_markup=await get_courier_management_keyboard()
        )
        return
    
    await message.answer(
        "Выберите курьера для удаления:",
        reply_markup=await get_couriers_list_keyboard(couriers)
    )
    
    await state.set_state(UserManagementForm.waiting_for_courier_deletion)


@router.message(F.text == "🗑️ Удалить магазин", StateFilter(None))
async def cmd_delete_shop_start(message: Message, state: FSMContext):
    """Handler to start shop deletion process"""
    if not await admin_access_required(message):
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    shops = await get_all_shops()
    
    if not shops:
        await message.answer(
            "Нет магазинов для удаления.",
            reply_markup=await get_shop_management_keyboard()
        )
        return
    
    await message.answer(
        "Выберите магазин для удаления:",
        reply_markup=await get_shops_list_keyboard(shops)
    )
    
    await state.set_state(UserManagementForm.waiting_for_shop_deletion)


@router.message(F.text == "⬅️ Назад", StateFilter(UserManagementForm.waiting_for_courier_deletion, UserManagementForm.waiting_for_shop_deletion))
async def cmd_back_to_user_management(message: Message, state: FSMContext):
    """Handler to return to user management menu"""
    if not await admin_access_required(message):
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    current_state = await state.get_state()
    
    await state.clear()
    
    if current_state == UserManagementForm.waiting_for_courier_deletion.state:
        await message.answer(
            "Вернулись в меню управления курьерами.",
            reply_markup=await get_courier_management_keyboard()
        )
    else:
        await message.answer(
            "Вернулись в меню управления магазинами.",
            reply_markup=await get_shop_management_keyboard()
        )


@router.message(UserManagementForm.waiting_for_courier_deletion)
async def process_courier_deletion(message: Message, state: FSMContext):
    """Handler for courier deletion"""
    if not await admin_access_required(message):
        await message.answer("Эта команда доступна только администраторам.")
        await state.clear()
        return
    
    if message.text == "⬅️ Назад":
        await cmd_back_to_user_management(message, state)
        return
    
    # Извлекаем ID пользователя из формата "❌ Имя (ID: 123456)"
    match = re.search(r'ID: (\d+)', message.text)
    if not match:
        await message.answer(
            "Пожалуйста, выберите курьера из списка кнопок.",
            reply_markup=await get_couriers_list_keyboard(await get_all_couriers())
        )
        return
    
    user_id = int(match.group(1))
    
    # Проверяем, есть ли у пользователя активные заказы
    has_orders = await check_user_has_orders(user_id)
    if has_orders:
        await message.answer(
            "Этот курьер имеет активные заказы. Сначала необходимо завершить все его заказы.",
            reply_markup=await get_courier_management_keyboard()
        )
        await state.clear()
        return
    
    # Сохраняем ID пользователя в состоянии и запрашиваем подтверждение
    await state.update_data(user_id=user_id)
    
    # Получаем имя пользователя
    all_couriers = await get_all_couriers()
    courier_name = next((c["username"] for c in all_couriers if c["id"] == user_id), "Unknown")
    
    await message.answer(
        f"Вы уверены, что хотите удалить курьера {courier_name} (ID: {user_id})?\n\n"
        "Отправьте 'Да' для подтверждения или 'Нет' для отмены."
    )
    
    await state.set_state(UserManagementForm.confirm_deletion)


@router.message(UserManagementForm.waiting_for_shop_deletion)
async def process_shop_deletion(message: Message, state: FSMContext):
    """Handler for shop deletion"""
    if not await admin_access_required(message):
        await message.answer("Эта команда доступна только администраторам.")
        await state.clear()
        return
    
    if message.text == "⬅️ Назад":
        await cmd_back_to_user_management(message, state)
        return
    
    # Извлекаем ID пользователя из формата "❌ Имя (ID: 123456)"
    match = re.search(r'ID: (\d+)', message.text)
    if not match:
        await message.answer(
            "Пожалуйста, выберите магазин из списка кнопок.",
            reply_markup=await get_shops_list_keyboard(await get_all_shops())
        )
        return
    
    user_id = int(match.group(1))
    
    # Проверяем, есть ли у пользователя активные заказы
    has_orders = await check_user_has_orders(user_id)
    if has_orders:
        await message.answer(
            "У этого магазина есть активные заказы. Сначала необходимо завершить все его заказы.",
            reply_markup=await get_shop_management_keyboard()
        )
        await state.clear()
        return
    
    # Сохраняем ID пользователя в состоянии и запрашиваем подтверждение
    await state.update_data(user_id=user_id)
    
    # Получаем имя пользователя
    all_shops = await get_all_shops()
    shop_name = next((s["username"] for s in all_shops if s["id"] == user_id), "Unknown")
    
    await message.answer(
        f"Вы уверены, что хотите удалить магазин {shop_name} (ID: {user_id})?\n\n"
        "Отправьте 'Да' для подтверждения или 'Нет' для отмены."
    )
    
    await state.set_state(UserManagementForm.confirm_deletion)


@router.message(UserManagementForm.confirm_deletion)
async def process_deletion_confirmation(message: Message, state: FSMContext):
    """Handler for deletion confirmation"""
    if not await admin_access_required(message):
        await message.answer("Эта команда доступна только администраторам.")
        await state.clear()
        return
    
    confirmation = message.text.lower()
    
    if confirmation not in ["да", "нет"]:
        await message.answer("Пожалуйста, отправьте 'Да' для подтверждения или 'Нет' для отмены.")
        return
    
    data = await state.get_data()
    user_id = data.get("user_id")
    
    if confirmation == "нет":
        await message.answer(
            "Удаление отменено.",
            reply_markup=await get_admin_main_keyboard()
        )
        await state.clear()
        return
    
    # Удаляем пользователя
    success = await delete_user(user_id)
    
    if not success:
        await message.answer(
            "Ошибка при удалении пользователя. Пожалуйста, попробуйте снова.",
            reply_markup=await get_admin_main_keyboard()
        )
    else:
        await message.answer(
            f"Пользователь (ID: {user_id}) успешно удален.",
            reply_markup=await get_admin_main_keyboard()
        )
    
    await state.clear()


@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_admin_help(message: Message):
    """Handler for /help command or Help button for admin users"""
    if not await admin_access_required(message):
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    help_text = (
        "🛠 <b>Команды администратора:</b>\n\n"
        "• 📋 <b>Список заказов</b> - просмотр всех ожидающих заказов\n"
        "• 📮 <b>Назначить заказ</b> - назначение заказов курьерам\n"
        "• 👥 <b>Управление пользователями</b> - управление белым списком, курьерами и магазинами\n"
        "• 📊 <b>Отчет</b> - просмотр статистики по заказам\n"
        "• ❓ <b>Помощь</b> - показать эту справку\n\n"
        "<b>Команды белого списка:</b>\n"
        "/whitelist_add ID - добавить пользователя в белый список\n"
        "/whitelist_list - просмотр пользователей в белом списке\n"
        "/whitelist_remove ID - удалить пользователя из белого списка\n"
        "/export_orders - экспорт заказов в Excel\n\n"
        "⏰ <b>Рабочие часы:</b> 10:00 - 20:00"
    )
    
    await message.answer(help_text, reply_markup=await get_admin_main_keyboard())


@router.message(Command("report"))
@router.message(F.text == "📊 Отчет")
async def cmd_report(message: Message):
    """Handler for /report command to generate delivery reports"""
    if not await admin_access_required(message):
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    # Get today's date and yesterday's date
    today = get_date_dushanbe()
    yesterday = get_yesterday_date()
    
    # Get all orders
    all_orders = await get_all_orders()
    total_orders = len(all_orders)
    
    # Count orders by status
    pending_count = 0
    assigned_count = 0
    delivered_count = 0
    
    for order in all_orders:
        status = order.get('status', 'pending')
        if status == 'pending':
            pending_count += 1
        elif status == 'assigned':
            assigned_count += 1
        elif status == 'delivered':
            delivered_count += 1
    
    # Get delivered orders for today and yesterday
    today_delivered = await get_delivered_orders_in_timeframe(today)
    yesterday_delivered = await get_delivered_orders_in_timeframe(yesterday)
    
    # Prepare report
    report = (
        "📊 Отчет о доставках\n\n"
        f"Всего заказов: {total_orders}\n"
        f"В ожидании: {pending_count}\n"
        f"Назначено: {assigned_count}\n"
        f"Доставлено: {delivered_count}\n\n"
        f"Доставлено сегодня ({today}): {len(today_delivered)}\n"
        f"Доставлено вчера ({yesterday}): {len(yesterday_delivered)}\n\n"
    )
    
    # Убрали отображение деталей доставленных заказов по просьбе клиента
    
    await message.answer(report, reply_markup=await get_admin_main_keyboard())


def register_handlers(dp: Router):
    """Register all admin handlers"""
    dp.include_router(router)
