from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Order
from utils.logger import get_logger, log_database_operation

logger = get_logger(__name__)

@log_database_operation
async def create_order(session: AsyncSession, order_data: dict) -> Order:
    order = Order(
        user_id=order_data['user_id'],
        username=order_data.get('username'),
        first_name=order_data['first_name'],
        phone_number=order_data['phone_number'],
        flight=order_data['flight'],
        address=order_data['address'],
        order_screenshot=order_data['order_screenshot'],
        payment_screenshot=order_data['payment_screenshot'],
        payment_status='pending',
        order_status='waiting_manager'
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    logger.info(f"💾 Создан новый заказ ID: {order.id} для пользователя {order.user_id}")
    return order

@log_database_operation
async def get_order_by_id(session: AsyncSession, order_id: int) -> Order:
    stmt = select(Order).where(Order.id == order_id)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()
    if order:
        logger.debug(f"📄 Получен заказ ID: {order_id}")
    else:
        logger.warning(f"⚠️ Заказ ID: {order_id} не найден")
    return order

@log_database_operation
async def get_orders_by_user_id(session: AsyncSession, user_id: int, limit: int = 10):
    stmt = select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    orders = result.scalars().all()
    logger.debug(f"📋 Получено {len(orders)} заказов для пользователя {user_id}")
    return orders

@log_database_operation
async def get_recent_orders(session: AsyncSession, limit: int = 10):
    stmt = select(Order).order_by(Order.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    orders = result.scalars().all()
    logger.debug(f"📋 Получено {len(orders)} последних заказов")
    return orders

@log_database_operation
async def update_order_status(session: AsyncSession, order_id: int, **kwargs) -> Order:
    order = await get_order_by_id(session, order_id)
    if order:
        changes = []
        for key, value in kwargs.items():
            old_value = getattr(order, key)
            setattr(order, key, value)
            changes.append(f"{key}: {old_value} -> {value}")
        
        await session.commit()
        await session.refresh(order)
        logger.info(f"🔄 Обновлен заказ ID: {order_id}. Изменения: {', '.join(changes)}")
    return order
