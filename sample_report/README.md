# Testing with a real blood test PDF

Use a digital PDF where text can be selected and copied. Scanned reports, screenshots, and handwritten pages are not supported in this version.

## Good report sources

- SRL Diagnostics
- Thyrocare
- Metropolis
- Apollo Diagnostics
- Lal PathLabs

## Quick test steps

1. Open the PDF and confirm you can highlight text.
2. Start the backend on port `8000`.
3. Start the frontend on port `5173`.
4. Upload the PDF in the app.
5. Review the extracted markers, status badges, and recommendations.

## If you do not have a real report

Create a simple text document with values like these and export it as a PDF:

```text
Patient: Test Patient
Age: 35 years
Gender: Male
Date: 2026-04-22

Hemoglobin: 11.2 g/dL
WBC: 9.5 x10^3/uL
Platelets: 145 x10^3/uL
Blood Sugar Fasting: 108 mg/dL
Total Cholesterol: 215 mg/dL
LDL: 145 mg/dL
HDL: 38 mg/dL
Triglycerides: 180 mg/dL
TSH: 5.2 mIU/L
Vitamin D: 14 ng/mL
Vitamin B12: 185 pg/mL
```

## Expected failure cases

- `Could not extract text. PDF may be scanned. Please use a text-based PDF.`
- `No recognizable blood test values found.`
- `AI analysis failed. Please try again.`
