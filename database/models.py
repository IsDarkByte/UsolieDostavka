from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String)
    first_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    flight = Column(String, nullable=False)
    address = Column(String, nullable=False)
    order_screenshot = Column(String)  # Скриншот заказа
    payment_screenshot = Column(String)  # Скриншот оплаты
    payment_status = Column(String, default='pending')
    order_status = Column(String, default='waiting_manager')
    manager_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    