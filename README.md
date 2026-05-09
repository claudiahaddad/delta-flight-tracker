# Delta Flight Tracker

Track Delta flight prices and get notified via email when they drop. Rebook at the lower price and pocket the credit.

## How It Works

1. **Enter your flight** — Add your booked Delta flight with the price you paid
2. **Monitor prices** — Manually update prices when you check Delta (automated checking coming soon)
3. **Get notified** — Receive email alerts when the price drops
4. **Rebook & save** — Cancel and rebook at the lower price, keeping the difference as credit

## Features

- Track multiple flights with price history
- Email notifications on price drops with direct Delta rebooking link
- Dashboard showing total savings across all flights
- Continuous tracking — if price drops from $300 → $200 → $150, you save at each step

## Setup

### Prerequisites

- Python 3.11+

### Installation

```bash
# Clone the repo
git clone https://github.com/claudiahaddad/delta-flight-tracker.git
cd delta-flight-tracker

# Install dependencies
pip install -e ".[dev]"

# (Optional) Configure email notifications
cp .env.example .env
# Edit .env with your SMTP credentials

# Run the app
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### Email Setup (Optional)

To receive email notifications when prices drop, create a `.env` file:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
NOTIFICATION_EMAIL=claudiaa6499@gmail.com
```

For Gmail, use an [App Password](https://myaccount.google.com/apppasswords) instead of your regular password.

Without email configured, price drops are still tracked and logged — you just won't get email alerts.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | Dashboard stats |
| POST | `/api/flights` | Add a flight to track |
| GET | `/api/flights` | List all tracked flights |
| GET | `/api/flights/:id` | Get flight details |
| POST | `/api/flights/:id/price` | Update price (triggers notification if lower) |
| GET | `/api/flights/:id/history` | Price history for a flight |
| PATCH | `/api/flights/:id/status?status=paused` | Pause/resume tracking |
| DELETE | `/api/flights/:id` | Delete a tracked flight |
| GET | `/api/notifications` | List price drop notifications |

## Roadmap

- [ ] Automated price checking via Google Flights / SerpAPI
- [ ] Scheduled background price checks
- [ ] Auto-rebook via Delta account integration
- [ ] Credit/eCredit tracking
- [ ] Multi-airline support
- [ ] Mobile-friendly PWA

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite
- **Frontend:** Vanilla HTML/CSS/JS
- **Email:** aiosmtplib (Gmail SMTP)
