from datetime import datetime

from pydantic import BaseModel, Field


class FlightCreate(BaseModel):
    origin: str = Field(
        ..., min_length=3, max_length=3, description="Origin airport code (e.g. JFK)"
    )
    destination: str = Field(
        ..., min_length=3, max_length=3, description="Destination airport code (e.g. LAX)"
    )
    departure_date: str = Field(..., description="Departure date (YYYY-MM-DD)")
    return_date: str | None = Field(None, description="Return date (YYYY-MM-DD)")
    confirmation_number: str | None = Field(None, description="Delta confirmation number")
    original_price: float = Field(..., gt=0, description="Price you paid or current price")
    cabin_class: str = Field("economy", description="Cabin class")
    passengers: int = Field(1, ge=1, description="Number of passengers")


class PriceUpdate(BaseModel):
    price: float = Field(..., gt=0, description="New price found")
    source: str = Field("manual", description="Source of price (manual, delta, google_flights)")


class FlightResponse(BaseModel):
    id: int
    origin: str
    destination: str
    departure_date: str
    return_date: str | None
    confirmation_number: str | None
    original_price: float
    current_price: float
    lowest_price: float
    total_savings: float
    status: str
    cabin_class: str
    passengers: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PriceRecordResponse(BaseModel):
    id: int
    flight_id: int
    price: float
    checked_at: datetime
    source: str

    model_config = {"from_attributes": True}


class NotificationResponse(BaseModel):
    id: int
    flight_id: int
    old_price: float
    new_price: float
    savings: float
    sent_at: datetime
    email_sent: int

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_flights_tracked: int
    active_flights: int
    total_savings: float
    total_notifications: int
