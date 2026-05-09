import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


class FlightStatus(str, enum.Enum):
    TRACKING = "tracking"
    PAUSED = "paused"
    EXPIRED = "expired"


class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    origin = Column(String(3), nullable=False)
    destination = Column(String(3), nullable=False)
    departure_date = Column(String, nullable=False)
    return_date = Column(String, nullable=True)
    confirmation_number = Column(String, nullable=True)
    original_price = Column(Float, nullable=False)
    booked_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    lowest_price = Column(Float, nullable=False)
    total_savings = Column(Float, default=0.0)
    status = Column(Enum(FlightStatus), default=FlightStatus.TRACKING)
    cabin_class = Column(String, default="economy")
    passengers = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    price_history = relationship(
        "PriceRecord", back_populates="flight", order_by="PriceRecord.checked_at"
    )


class PriceRecord(Base):
    __tablename__ = "price_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False)
    price = Column(Float, nullable=False)
    checked_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String, default="manual")

    flight = relationship("Flight", back_populates="price_history")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False)
    old_price = Column(Float, nullable=False)
    new_price = Column(Float, nullable=False)
    savings = Column(Float, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    email_sent = Column(Integer, default=0)


engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
