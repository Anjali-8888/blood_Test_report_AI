# Blood Test Analysis and Health Recommendation System

This project accepts a blood test PDF, extracts marker values, classifies them against reference ranges, and returns general wellness recommendations in a React UI. It is stateless, uses no database, avoids OCR, and makes only two Gemini API calls per analysis: one for value extraction and one for recommendation generation.

Medical disclaimer: This tool provides general health information only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider.

## What it does

1. Upload a blood test PDF from the frontend.
2. Attempt native text extraction from the PDF using PyMuPDF.
3. Send the PDF itself, plus any native extracted text, to Gemini to normalize blood-marker values into JSON.
4. Classify each value as normal, low, high, or unknown using Python logic.
5. Send abnormal values to Gemini for general wellness recommendations.
6. Show the results in a React dashboard with color-coded indicators.

## Tech stack

- Backend: FastAPI, PyMuPDF, google-genai, optional Hugging Face OCR, Pydantic, python-dotenv, Uvicorn
- Frontend: React 18, Vite, Axios, plain CSS
- AI provider: Google Gemini

## Project structure

```text
blood-test-analysis/
├── backend/
│   ├── main.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── extractor.py
│   │   ├── analyzer.py
│   │   └── recommender.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py
│   │   └── reference_ranges.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.jsx
│   │   │   ├── ResultCard.jsx
│   │   │   ├── BloodMarkerTable.jsx
│   │   │   └── RecommendationList.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles/
│   │       └── global.css
│   ├── index.html
│   └── package.json
├── sample_report/
│   └── README.md
└── README.md
```

## Setup

### Backend

```bash
cd /Users/gauravkumar/Downloads/blood_Test_report_AI-main/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `/Users/gauravkumar/Downloads/blood_Test_report_AI-main/backend/.env`:

```env
GEMINI_API_KEY=your_real_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
HF_TOKEN=your_optional_huggingface_token
HF_OCR_MODEL=microsoft/trocr-base-printed
HF_OCR_MAX_PAGES=3
MAX_FILE_SIZE_MB=10
CORS_ORIGINS=http://localhost:5173
```

Run the backend on port `8000`:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd /Users/gauravkumar/Downloads/blood_Test_report_AI-main/frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

## How to get a Gemini API key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Create a new API key.
3. Add it to `backend/.env` as `GEMINI_API_KEY`.

## How to test locally

1. Start the backend on `http://localhost:8000`.
2. Start the frontend on `http://localhost:5173`.
3. Open the frontend in your browser.
4. Upload a real text-based blood test PDF.
5. Optionally select gender for gender-specific reference ranges.
6. Click `Analyze report`.

Indian lab PDFs from SRL, Thyrocare, Metropolis, Apollo, and Lal PathLabs usually work best when they are digital PDFs and not scanned images.

## Manual setup required

- Create `backend/.env` from `.env.example`
- Add your `GEMINI_API_KEY`
- Keep backend running on port `8000`
- Keep frontend running on port `5173`

## Known limitations

- Scanned or image-heavy PDFs can use Gemini document understanding and an optional Hugging Face OCR fallback, but badly blurred or low-quality scans may still fail.
- Handwritten reports are not supported.
- Extraction quality depends on the PDF text quality and report layout.
- Unusual lab-specific units may not always convert perfectly.
- Recommendations are general wellness guidance only and must not be treated as diagnosis.

## End-to-end flow

The full intended flow is:

1. `POST /analyze` receives the uploaded PDF.
2. `backend/utils/pdf_parser.py` attempts native text extraction.
3. `backend/agents/extractor.py` sends the PDF itself, plus any extracted text hint, to Gemini and gets structured markers.
4. `backend/agents/analyzer.py` classifies values in Python using `reference_ranges.py`.
5. `backend/agents/recommender.py` sends only the interpreted context to Gemini.
6. The frontend renders the summary, sorted marker table, and recommendation cards.

## Should we use RAG or OCR?

For this version, no.

- Traditional OCR is not required because Gemini document understanding can process both embedded-text PDFs and many scanned PDF reports directly.
- RAG is not needed because the system analyzes one uploaded report at a time and uses a fixed in-code reference-range dataset.
- Adding RAG would increase complexity without helping the main workflow much.

If you later want doctor-facing clinical references, multilingual support, or guideline-backed explanation links, we can add a small curated knowledge layer. For the current scope, simple stateless processing is the better design.
