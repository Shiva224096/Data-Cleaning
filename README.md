# DataScrub — Intelligent Data Cleaning

A modern web application that helps users analyze, identify issues in, and clean their Excel/CSV data through a step-by-step wizard interface.

![DataScrub](https://img.shields.io/badge/DataScrub-v1.0-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Python](https://img.shields.io/badge/python-3.13-yellow) ![React](https://img.shields.io/badge/react-18-cyan)

## Features

- **Step-by-Step Wizard** — Guided 6-step workflow from upload to export
- **ML Column Detection** — Automatically predicts column types (Email, Phone, IBAN, Date, etc.)
- **25+ Data Validators** — Email, phone, company fuzzy match, IBAN, credit card, PAN, GST, SSN, UUID, ISBN, VIN, and more
- **Interactive Dashboard** — Visual summary with drill-down charts
- **Excel-like Grid** — AG Grid with inline editing, filtering, sorting, and issue highlighting
- **Smart Export** — Appends `DataScrub_Issue_Status` column showing all issues per row
- **Dark Mode UI** — Premium glassmorphism design with micro-animations

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite |
| Data Grid | AG Grid Community (MIT) |
| Charts | Recharts |
| Backend | FastAPI (Python 3.13) |
| Validation | phonenumbers, python-stdnum, TheFuzz, email-validator |
| ML | scikit-learn RandomForest + heuristics |

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.13

### 1. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at **http://localhost:3000**

## Project Structure

```
├── frontend/               # React + Vite SPA
│   ├── src/
│   │   ├── components/
│   │   │   ├── Wizard/         # Step indicator
│   │   │   ├── FileUpload/     # Drag & drop upload
│   │   │   ├── Profiling/      # ML scanning loader
│   │   │   ├── ColumnMapping/  # Column type assignment
│   │   │   ├── CleaningProgress/ # Real-time progress
│   │   │   ├── Dashboard/      # Issue summary & charts
│   │   │   ├── DataGrid/       # AG Grid spreadsheet
│   │   │   └── Export/         # Download clean data
│   │   └── utils/api.js        # API client
│   └── vite.config.js          # Proxy to backend
│
├── backend/                # FastAPI Python API
│   ├── routers/            # API endpoints
│   ├── services/           # Business logic
│   ├── validators/         # 14 validator modules
│   ├── ml/                 # Column type classifier
│   └── main.py             # App entry point
```

## Supported Data Types

| Category | Types |
|----------|-------|
| Personal | Email, Mobile Phone, Landline, First/Last Name, Zip Code |
| Business | Company Name (fuzzy), IBAN, Credit Card, Currency, PAN, GST, SSN |
| Web | URL, IPv4, IPv6, MAC Address, Hex Color |
| General | UUID, ISBN, VIN, String, Integer, Float, Date/Time |

## License

MIT — All libraries used are free and open-source.
