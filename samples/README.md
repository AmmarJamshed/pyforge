# PyForge test samples

## QuickCalc (recommended)

- **App name:** `QuickCalc`
- **Target:** Windows EXE (or any desktop target)
- **What it does:** Menu-driven calculator (add / subtract / multiply / divide)

On Render (cloud), you get an AI-prepared **ZIP** to run locally. On a VPS with Docker, you get a real `.exe`.

## Tip Calculator

- **App name:** `TipCalc`
- **Target:** Windows EXE
- **What it does:** Bill + tip + split between people

## How to test on https://pyforge-web.onrender.com

1. Open the app (wait ~30s if the API was sleeping).
2. Pick **QuickCalc** from the Sample dropdown.
3. Set app name to **QuickCalc**.
4. Choose **Windows EXE**.
5. Click **Build with AI**.
6. Download the ZIP when finished; run `python main.py` inside to try the calculator.
