import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Flight, FlightStatus, Notification, PriceRecord, get_db
from app.notifications import send_price_drop_notification_sync
from app.schemas import (
    DashboardStats,
    FlightCreate,
    FlightResponse,
    NotificationResponse,
    PriceRecordResponse,
    PriceUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/dashboard", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)):
    total = db.query(func.count(Flight.id)).scalar() or 0
    active = (
        db.query(func.count(Flight.id)).filter(Flight.status == FlightStatus.TRACKING).scalar() or 0
    )
    savings = db.query(func.sum(Flight.total_savings)).scalar() or 0.0
    notifs = db.query(func.count(Notification.id)).scalar() or 0
    return DashboardStats(
        total_flights_tracked=total,
        active_flights=active,
        total_savings=savings,
        total_notifications=notifs,
    )


@router.post("/api/flights", response_model=FlightResponse)
def create_flight(flight: FlightCreate, db: Session = Depends(get_db)):
    db_flight = Flight(
        origin=flight.origin.upper(),
        destination=flight.destination.upper(),
        departure_date=flight.departure_date,
        return_date=flight.return_date,
        confirmation_number=flight.confirmation_number,
        original_price=flight.original_price,
        current_price=flight.original_price,
        lowest_price=flight.original_price,
        cabin_class=flight.cabin_class,
        passengers=flight.passengers,
    )
    db.add(db_flight)
    db.commit()
    db.refresh(db_flight)

    price_record = PriceRecord(
        flight_id=db_flight.id,
        price=flight.original_price,
        source="initial",
    )
    db.add(price_record)
    db.commit()

    logger.info(
        "Created flight %s→%s at $%.2f",
        db_flight.origin,
        db_flight.destination,
        db_flight.original_price,
    )
    return db_flight


@router.get("/api/flights", response_model=list[FlightResponse])
def list_flights(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Flight).order_by(Flight.created_at.desc())
    if status:
        query = query.filter(Flight.status == status)
    return query.all()


@router.get("/api/flights/{flight_id}", response_model=FlightResponse)
def get_flight(flight_id: int, db: Session = Depends(get_db)):
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    return flight


@router.post("/api/flights/{flight_id}/price", response_model=PriceRecordResponse)
def update_price(flight_id: int, price_update: PriceUpdate, db: Session = Depends(get_db)):
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    old_price = flight.current_price
    new_price = price_update.price

    price_record = PriceRecord(
        flight_id=flight_id,
        price=new_price,
        source=price_update.source,
    )
    db.add(price_record)

    flight.current_price = new_price
    flight.updated_at = datetime.utcnow()

    if new_price < old_price:
        savings = old_price - new_price
        flight.total_savings += savings

        if new_price < flight.lowest_price:
            flight.lowest_price = new_price

        notification = Notification(
            flight_id=flight_id,
            old_price=old_price,
            new_price=new_price,
            savings=savings,
        )

        email_sent = send_price_drop_notification_sync(
            origin=flight.origin,
            destination=flight.destination,
            departure_date=flight.departure_date,
            old_price=old_price,
            new_price=new_price,
            savings=savings,
            total_savings=flight.total_savings,
            confirmation_number=flight.confirmation_number,
        )
        notification.email_sent = 1 if email_sent else 0
        db.add(notification)

        logger.info(
            "Price drop for %s→%s: $%.2f → $%.2f (save $%.2f)",
            flight.origin,
            flight.destination,
            old_price,
            new_price,
            savings,
        )

    db.commit()
    db.refresh(price_record)
    return price_record


@router.get("/api/flights/{flight_id}/history", response_model=list[PriceRecordResponse])
def get_price_history(flight_id: int, db: Session = Depends(get_db)):
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    return flight.price_history


@router.patch("/api/flights/{flight_id}/status")
def update_flight_status(flight_id: int, status: str, db: Session = Depends(get_db)):
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    try:
        flight.status = FlightStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    flight.updated_at = datetime.utcnow()
    db.commit()
    return {"message": f"Flight status updated to {status}"}


@router.delete("/api/flights/{flight_id}")
def delete_flight(flight_id: int, db: Session = Depends(get_db)):
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    db.query(PriceRecord).filter(PriceRecord.flight_id == flight_id).delete()
    db.query(Notification).filter(Notification.flight_id == flight_id).delete()
    db.delete(flight)
    db.commit()
    return {"message": "Flight deleted"}


@router.get("/api/notifications", response_model=list[NotificationResponse])
def list_notifications(flight_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Notification).order_by(Notification.sent_at.desc())
    if flight_id:
        query = query.filter(Notification.flight_id == flight_id)
    return query.limit(50).all()
