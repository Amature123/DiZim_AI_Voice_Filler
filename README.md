# DiZim AI — Viettel Invoice Assistant

An AI-powered system that automates VAT invoice issuance to Viettel S-Invoice from voice or text input.

---

## Architecture Overview

```
Voice / Text Input
        │
        ▼
┌───────────────────┐     ┌──────────────────────────┐
│  Web Speech API   │     │  Qwen3-ASR-0.6B (local)  │
│  (browser-side)   │     │  asr_service/ — port 8001 │
└────────┬──────────┘     └────────────┬─────────────┘
         └──────────────┬──────────────┘
                        │ text
                        ▼
              ┌──────────────────┐
              │ POST /api/extract │
              │  Qwen-Max LLM    │
              │ (DashScope Intl)  │
              └────────┬─────────┘
                       │ Viettel JSON
                       ▼
              ┌──────────────────────┐
              │ POST /api/invoice/   │
              │       publish        │
              │  1. validate + calc  │
              │  2. Viettel S-Invoice│
              │  3. generate PDF     │
              │  4. save to SQLite   │
              └────────┬─────────────┘
                       │
              ┌────────┴─────────────┐
              │  Response            │
              │  • invoice_no        │
              │  • PDF download link │
              └──────────────────────┘
```

---

## How It Works

### Step 1 — Input: Voice or Text

Two input modes are supported:

| Mode | Description |
|------|-------------|
| **Web Speech API** | Click the mic button in Chrome/Edge. Audio is transcribed directly in the browser — no server needed. |
| **Local ASR** | Toggle "Local ASR" and click mic. Audio is sent to `asr_service` (Qwen3-ASR-0.6B on port 8001) for higher-quality, offline transcription. |

Users can also type directly into the text area.

---

### Step 2 — Field Extraction (`POST /api/extract`)

The backend calls **Qwen-Max** via DashScope International using the OpenAI SDK. The LLM is guided by a structured prompt to return a Viettel S-Invoice-compatible JSON with:

- `buyerInfo` — buyer name, tax code, address, email, etc.
- `generalInvoiceInfo` — payment method, currency
- `itemInfo` — list of goods/services (name, unit, quantity, unit price, tax rate)

> The LLM only extracts data — all monetary calculations are recalculated server-side in Step 3.

---

### Step 3 — Invoice Publication (`POST /api/invoice/publish`)

Four sequential operations:

#### 3a. Validate & Recalculate (`lib/viettel.py`)
- Recalculates `itemTotalAmountWithoutTax = quantity × unitPrice`
- Computes `taxAmount` (defaults to 8% VAT if not specified)
- Builds `summarizeInfo` (subtotal, tax total, grand total in Vietnamese words)
- Groups `taxBreakdowns` by tax rate

#### 3b. Submit to Viettel S-Invoice API
- Adds required Viettel fields: `invoiceType`, `templateCode`, `invoiceSeries`, `transactionUuid`, etc.
- POSTs to `https://api-vinvoice.viettel.vn/.../createInvoice/{MST}` with HTTP Basic Auth
- **Non-fatal:** if Viettel returns an error, PDF is still generated and `viettel_error` is returned in the response

#### 3c. Generate PDF (`lib/invoice_pdf.py`)
- Uses **fpdf2** to render an invoice table layout
- Auto-detects Vietnamese-capable fonts (Arial, Tahoma, DejaVu) on Windows/Linux/Mac
- PDF saved to `outputs/{run_id}/invoice.pdf`

#### 3d. Save to SQLite (`lib/database.py`)
- Writes a record to the `documents` table (SQLite at `data/app.db`)
- History accessible via `GET /api/history`

---

### Step 4 — Download PDF

After successful publication, the frontend shows:
- Invoice number, transaction ID, and reservation code (from Viettel)
- A **Download PDF** button → `GET /api/invoice/pdf/{run_id}`

---

## Project Structure

```
dizim_AGAIN/
├── backend/
│   ├── main.py               # FastAPI app, serves frontend at GET /
│   ├── models.py             # Pydantic request/response schemas
│   ├── seed.py               # Seeds hoa-don-gtgt template into DB on startup
│   ├── requirements.txt
│   ├── .env                  # Environment variables (gitignored)
│   ├── .env.example
│   ├── api/
│   │   ├── extract.py        # POST /api/extract — LLM field extraction
│   │   ├── invoice.py        # POST /api/invoice/publish + GET /api/invoice/pdf/{id}
│   │   ├── transcribe.py     # POST /api/transcribe — proxy to ASR :8001
│   │   └── history.py        # GET /api/history
│   ├── lib/
│   │   ├── dashscope.py      # Qwen-Max client (OpenAI SDK + DashScope Intl)
│   │   ├── viettel.py        # Validate, calculate, call Viettel API
│   │   ├── invoice_pdf.py    # PDF generation with fpdf2
│   │   ├── prompts.py        # Viettel JSON extraction prompt
│   │   └── database.py       # SQLite CRUD via aiosqlite
│   └── tests/
│       ├── test_dashscope.py
│       ├── test_viettel.py
│       └── test_invoice_pdf.py
├── asr_service/
│   ├── main.py               # Qwen3-ASR-0.6B microservice (port 8001)
│   └── requirements.txt
├── frontend/
│   └── index.html            # Single-page app (Alpine.js CDN, no build step)
├── outputs/                  # Generated PDFs, one folder per run_id
├── data/
│   └── app.db                # SQLite database
└── venv/                     # Python virtual environment
```

---

## Setup & Running

### Prerequisites

- Python 3.11+
- Chrome or Edge (for Web Speech API mic input)
- (Optional) NVIDIA GPU to speed up local ASR

### 1. Backend

```bash
cd ./backend

# Install dependencies into the project venv
../venv/Scripts/pip install -r requirements.txt

# Create .env from example and fill in your credentials
cp .env.example .env

# Start the server
../venv/Scripts/uvicorn main:app --reload
```

Open `http://localhost:8000` — the frontend is served at `/`.

### 2. ASR Service (optional)

Only needed if you want to use Qwen3-ASR instead of the browser's Web Speech API.

```bash
# Create a separate conda environment
conda create -n qwen3-asr python=3.12 -y
conda activate qwen3-asr
pip install -r asr_service/requirements.txt

# Download the model (~1.2 GB) 
pip install huggingface_hub
hf download Qwen/Qwen3-ASR-0.6B --local-dir ./Qwen3-ASR-0.6B

# Start the service
uvicorn asr_service.main:app --host 0.0.0.0 --port 8001
```

---

## Environment Variables (`.env`)

| Variable | Description |
|----------|-------------|
| `DASHSCOPE_API_KEY` | Alibaba Cloud DashScope API key |
| `DASHSCOPE_BASE_URL` | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` |
| `VIETTEL_MST` | Business tax code (MST) |
| `VIETTEL_USER` | Viettel S-Invoice username (usually same as MST) |
| `VIETTEL_PASS` | Viettel S-Invoice password |
| `VIETTEL_API_BASE` | `https://api-vinvoice.viettel.vn` |
| `VIETTEL_INVOICE_SERIES` | Invoice series code (e.g. `C25TYY`) |
| `VIETTEL_TEMPLATE_CODE` | Invoice template code (e.g. `1/001`) |

Viettel credentials entered in the frontend config panel override `.env` values.

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serves `frontend/index.html` |
| `POST` | `/api/transcribe` | Forward audio to local ASR (port 8001) |
| `POST` | `/api/extract` | Text → Viettel JSON via Qwen-Max LLM |
| `POST` | `/api/invoice/publish` | Validate → Viettel API → PDF → save to DB |
| `GET` | `/api/invoice/pdf/{run_id}` | Download generated invoice PDF |
| `GET` | `/api/history` | List previously issued invoices |

---

## Running Tests

```bash
cd backend
../venv/Scripts/python -m pytest tests/ -v
```

7 tests passing:
- `test_dashscope.py` (3) — JSON parsing, missing API key handling
- `test_viettel.py` (3) — line item math, default tax rate, Vietnamese number-to-words
- `test_invoice_pdf.py` (1) — smoke test that a valid PDF file is produced

---

## Team

| Member | Contribution |
|--------|-------------|
| **Hiep** | Viettel S-Invoice API pipeline, invoice validation & calculation logic |
| **Phu** | Local ASR microservice (Qwen3-ASR-0.6B, port 8001) |
| **Tai** | FastAPI backend integration, Alpine.js frontend, PDF generation, DevOps |
