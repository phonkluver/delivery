"""
Handlers for courier users.
This module contains handlers for courier-specific commands and functions.
"""
import logging
from utils.timezone import format_datetime_dushanbe, is_working_hours, get_working_hours_message
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config import ROLE_COURIER, ADMIN_CHAT_IDS
from keyboards.courier_kb import get_delivery_confirmation_keyboard, get_courier_main_keyboard
from storage.database import (
    get_user_role, get_courier_orders, get_order_by_id, 
    mark_order_as_delivered
)

logger = logging.getLogger(__name__)

# Create router
router = Router()


class DeliveryCommentForm(StatesGroup):
    """States for delivery comment process"""
    waiting_for_comment = State()


async def courier_access_required(message: Message):
    """Check if user has courier role"""
    user_id = message.from_user.id
    role = await get_user_role(user_id)
    return role == ROLE_COURIER


@router.message(Command("mydeliveries"))
@router.message(F.text == "🚚 Мои доставки")
async def cmd_my_deliveries(message: Message):
    """Handler for /mydeliveries command to view assigned deliveries"""
    if not await courier_access_required(message):
        await message.answer("❌ Эта команда доступна только курьерам. Пожалуйста, зарегистрируйтесь как курьер.")
        return
    
    user_id = message.from_user.id
    orders = await get_courier_orders(user_id)
    
    if not orders:
        await message.answer(
            "📭 <b>У вас нет назначенных доставок.</b>\n\n"
            "Когда администратор назначит вам доставку, вы получите уведомление.",
            reply_markup=await get_courier_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    delivered_orders = []
    assigned_orders = []
    
    for order in orders:
        if order['status'] == "delivered":
            delivered_orders.append(order)
        elif order['status'] == "assigned":
            assigned_orders.append(order)
    
    # First, show active assignments with confirmation buttons
    for order in assigned_orders:
        # Форматируем сумму оплаты
        payment_amount = order.get('payment_amount', 0)
        payment_formatted = f"{payment_amount:.2f}" if payment_amount > 0 else "Нет"
        
        response = (
            f"🚚 <b>Активная доставка: Заказ #{order['id']}</b>\n\n"
            f"🏪 <b>Магазин:</b> {order['shop_name']}\n"
            f"📱 <b>Клиент:</b> {order['customer_phone']}\n"
            f"📍 <b>Адрес:</b> {order['city']}, {order['delivery_address']}\n"
            f"💰 <b>Сумма к оплате:</b> {payment_formatted} сомони\n"
            f"🕒 <b>Назначен:</b> {order.get('assigned_at', 'Н/Д')}\n\n"
            f"Нажмите кнопку <b>✅ Доставлено</b>, когда заказ будет доставлен клиенту."
        )
        
        await message.answer(
            response, 
            reply_markup=await get_delivery_confirmation_keyboard(order['id']),
            parse_mode="HTML"
        )
    
    # Then, show completed deliveries if any
    if delivered_orders:
        response = "✅ <b>Выполненные доставки:</b>\n\n"
        for order in delivered_orders:
            # Форматируем сумму оплаты
            payment_amount = order.get('payment_amount', 0)
            payment_formatted = f"{payment_amount:.2f}" if payment_amount > 0 else "Нет"
            
            response += (
                f"🟢 <b>Заказ #{order['id']}</b>\n"
                f"🏪 Магазин: {order['shop_name']}\n"
                f"📱 Клиент: {order['customer_phone']}\n"
                f"📍 Адрес: {order['city']}, {order['delivery_address']}\n"
                f"💰 Сумма к оплате: {payment_formatted} сомони\n"
                f"🕒 Доставлен в: {order.get('delivered_at', 'Н/Д')}\n\n"
            )
        
        await message.answer(
            response, 
            reply_markup=await get_courier_main_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("delivery:"))
async def delivery_confirmation_callback(callback_query: CallbackQuery, state: FSMContext):
    """Handle delivery confirmation button callbacks"""
    await callback_query.answer()
    
    # Extract order ID from callback data
    # Format: "delivery:confirm:123" or "delivery:comment:123"
    data_parts = callback_query.data.split(":")
    if len(data_parts) != 3:
        await callback_query.message.answer("Неверные данные обратного вызова")
        return
    
    action = data_parts[1]
    order_id = int(data_parts[2])
    
    # Get order details
    order = await get_order_by_id(order_id)
    
    if not order:
        await callback_query.message.answer("Заказ не найден")
        return
    
    # Check if the courier is assigned to this order
    courier_id = callback_query.from_user.id
    if order.get('courier_id') != courier_id:
        await callback_query.message.answer("Вы не назначены на этот заказ")
        return
    
    if action == "confirm":
        # Show final confirmation
        confirmation_kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text=f"Да, я доставил заказ #{order_id}"), KeyboardButton(text="Нет, еще не доставил")]
        ], resize_keyboard=True)
        
        await callback_query.message.answer(
            f"❓ <b>Вы уверены, что доставили заказ #{order_id}?</b>\n\n"
            f"Нажмите <b>Да</b> для подтверждения доставки или <b>Нет</b> для отмены.",
            reply_markup=confirmation_kb,
            parse_mode="HTML"
        )
    
    elif action == "comment":
        # Ask for delivery comment
        await callback_query.message.answer(
            f"📝 <b>Комментарий к заказу #{order_id}</b>\n\n"
            f"Пожалуйста, введите свой комментарий о проблеме или особенностях этой доставки. "
            f"Этот комментарий будет отправлен администратору и магазину.",
            parse_mode="HTML"
        )
        
        # Set state to wait for comment
        await state.set_state(DeliveryCommentForm.waiting_for_comment)
        await state.update_data(order_id=order_id)


# Обработчик для подтверждения доставки заказа
@router.message(lambda message: message.text and (message.text.startswith("Да, я доставил заказ #") or message.text == "Нет, еще не доставил"))
async def process_final_confirmation(message: Message, state: FSMContext):
    """Process final delivery confirmation"""
    logger.debug(f"Received message text: '{message.text}'")
    
    if message.text.startswith("Да, я доставил заказ #"):
        logger.debug(f"Message matches delivery confirmation pattern")
        try:
            # Extract order ID from the message
            parts = message.text.split("#")
            if len(parts) < 2:
                logger.error(f"Invalid format: no '#' character in message: {message.text}")
                await message.answer(
                    "❌ Неверный формат подтверждения. Не удалось найти идентификатор заказа.",
                    reply_markup=await get_courier_main_keyboard()
                )
                return
                
            order_id_text = parts[1].strip()
            logger.debug(f"Extracted order ID text: '{order_id_text}'")
            
            # Попытка преобразовать ID заказа в число
            try:
                order_id = int(order_id_text)
            except ValueError:
                logger.error(f"Cannot convert '{order_id_text}' to integer")
                await message.answer(
                    f"❌ Неверный формат ID заказа: '{order_id_text}'. Должно быть число.",
                    reply_markup=await get_courier_main_keyboard()
                )
                return
            
            logger.info(f"Processing delivery confirmation for order #{order_id}")
            
            # Mark order as delivered
            current_time = format_datetime_dushanbe()
            logger.debug(f"Marking order #{order_id} as delivered at {current_time}")
            
            success = await mark_order_as_delivered(
                order_id=order_id,
                delivered_at=current_time
            )
            
            if not success:
                logger.error(f"Failed to mark order #{order_id} as delivered")
                await message.answer(
                    "❌ Не удалось отметить заказ как доставленный. Пожалуйста, попробуйте еще раз.",
                    reply_markup=await get_courier_main_keyboard(),
                    parse_mode="HTML"
                )
                return
            
            await message.answer(
                f"✅ <b>Заказ #{order_id} отмечен как доставленный!</b>\n\n"
                f"Время доставки: {current_time}",
                reply_markup=await get_courier_main_keyboard(),
                parse_mode="HTML"
            )
            
            # Get order details to notify admin and shop
            order = await get_order_by_id(order_id)
            if not order:
                logger.error(f"Order #{order_id} not found after marking as delivered")
                return
            
            # Prepare notification message
            # Форматируем сумму оплаты
            payment_amount = order.get('payment_amount', 0)
            payment_formatted = f"{payment_amount:.2f}" if payment_amount > 0 else "Нет"
            
            delivery_notification = (
                f"✅ <b>Заказ #{order_id} доставлен!</b>\n\n"
                f"🏪 Магазин: {order['shop_name']}\n"
                f"📱 Клиент: {order['customer_phone']}\n"
                f"📍 Адрес: {order['city']}, {order['delivery_address']}\n"
                f"💰 Сумма к оплате: {payment_formatted} сомони\n"
                f"🕒 Доставлен в: {current_time}\n"
                f"🚚 Курьер: {order.get('courier_name', 'Н/Д')}"
            )
            
            # Notify admin
            bot = message.bot
            for admin_id in ADMIN_CHAT_IDS:
                try:
                    await bot.send_message(admin_id, delivery_notification, parse_mode="HTML")
                    logger.info(f"Notification sent to admin {admin_id}")
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
            
            # Notify shop
            shop_id = order.get('shop_id')
            if shop_id:
                try:
                    await bot.send_message(shop_id, delivery_notification, parse_mode="HTML")
                    logger.info(f"Notification sent to shop {shop_id}")
                except Exception as e:
                    logger.error(f"Failed to notify shop {shop_id}: {e}")
                    

            
        except Exception as e:
            logger.error(f"Unexpected error processing delivery confirmation: {e}", exc_info=True)
            await message.answer(
                "❌ Произошла ошибка при обработке подтверждения доставки. Пожалуйста, попробуйте еще раз.",
                reply_markup=await get_courier_main_keyboard(),
                parse_mode="HTML"
            )
    
    elif message.text == "Нет, еще не доставил":
        logger.debug("User declined delivery confirmation")
        await message.answer(
            "🔄 Подтверждение доставки отменено. Вы можете подтвердить доставку позже.",
            reply_markup=await get_courier_main_keyboard(),
            parse_mode="HTML"
        )
    
    # Clear state regardless of the outcome
    await state.clear()


@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_courier_help(message: Message):
    """Handler for /help command or Help button for courier users"""
    if not await courier_access_required(message):
        await message.answer("Эта команда доступна только курьерам. Пожалуйста, зарегистрируйтесь как курьер.")
        return
    
    help_text = (
        "🚚 <b>Инструкция для курьера</b>\n\n"
        "<b>Доступные команды:</b>\n"
        "• 🚚 <b>Мои доставки</b> - просмотр всех ваших активных и выполненных доставок\n"
        "• ❓ <b>Помощь</b> - показать эту справку\n\n"
        "<b>Процесс доставки:</b>\n"
        "1. Когда вам назначат заказ, вы получите уведомление с деталями доставки.\n"
        "2. Доставьте заказ по указанному адресу.\n"
        "3. После доставки нажмите кнопку <b>✅ Доставлено</b>.\n"
        "4. Подтвердите доставку, нажав <b>Да, я доставил заказ</b>.\n\n"
        "<b>Возникли проблемы?</b>\n"
        "Если возникли сложности с доставкой, используйте кнопку <b>💬 Добавить комментарий</b>, чтобы сообщить о ситуации.\n\n"
        "<b>Режим работы:</b> 10:00 - 20:00\n"
        "По всем вопросам обращайтесь к администратору."
    )
    
    await message.answer(help_text, reply_markup=await get_courier_main_keyboard(), parse_mode="HTML")


@router.message(DeliveryCommentForm.waiting_for_comment)
async def process_delivery_comment(message: Message, state: FSMContext):
    """Process delivery comment"""
    data = await state.get_data()
    order_id = data.get('order_id')
    
    if not order_id:
        await message.answer("❌ <b>Ошибка:</b> Не найден ID заказа.")
        await state.clear()
        return
    
    comment = message.text
    
    # Get order details
    order = await get_order_by_id(order_id)
    
    if not order:
        await message.answer("❌ <b>Ошибка:</b> Заказ не найден.")
        await state.clear()
        return
    
    logger.info(f"Processing comment for order #{order_id}: {comment[:50]}...")
    
    # Save comment (you would need to extend your database functions to handle comments)
    # For now, we'll just acknowledge the comment
    
    await message.answer(
        f"✅ <b>Комментарий к заказу #{order_id} записан!</b>\n\n"
        f"Пожалуйста, подтвердите доставку, когда заказ будет доставлен.",
        reply_markup=await get_delivery_confirmation_keyboard(order_id),
        parse_mode="HTML"
    )
    
    # Notify admin about the comment
    comment_notification = (
        f"💬 <b>Комментарий к заказу #{order_id}</b>\n\n"
        f"🚚 <b>Курьер:</b> {message.from_user.full_name}\n"
        f"📝 <b>Комментарий:</b> {comment}\n\n"
        f"📦 <b>Заказ:</b> {order.get('shop_name', 'Н/Д')} → {order.get('city', 'Н/Д')}, {order.get('delivery_address', 'Н/Д')}"
    )
    
    # Send to admins
    bot = message.bot
    for admin_id in ADMIN_CHAT_IDS:
        try:
            await bot.send_message(admin_id, comment_notification, parse_mode="HTML")
            logger.info(f"Comment notification sent to admin {admin_id}")
        except Exception as e:
            logger.error(f"Failed to send comment to admin {admin_id}: {e}")
    
    # Notify shop about the comment
    shop_id = order.get('shop_id')
    if shop_id:
        try:
            await bot.send_message(shop_id, comment_notification, parse_mode="HTML")
            logger.info(f"Comment notification sent to shop {shop_id}")
        except Exception as e:
            logger.error(f"Failed to send comment to shop {shop_id}: {e}")
    
    await state.clear()


def register_handlers(dp: Router):
    """Register all courier handlers"""
    dp.include_router(router)
