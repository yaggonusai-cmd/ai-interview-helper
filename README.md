# AI Interview Helper

A Python + Streamlit interview practice application for IT/software roles.

## Features

- Choose your target IT/software role.
- Choose interview type and experience level.
- Generate realistic interview questions.
- Submit your answer.
- Receive an overall score and category scores.
- See strengths, missing points and improvements.
- Get a stronger sample interview answer.
- Receive a realistic follow-up question.
- Track practice-session scores.

## 1. Install Python

Use Python 3.10 or newer.

Check:

```powershell
python --version
```

## 2. Open the project

```powershell
cd ai_interview_helper
```

## 3. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

## 4. Install packages

```powershell
pip install -r requirements.txt
```

## 5. Set your OpenAI API key

For the current PowerShell window:

```powershell
$env:OPENAI_API_KEY="YOUR_API_KEY"
```

Optional model setting:

```powershell
$env:OPENAI_MODEL="gpt-5.6"
```

Never commit your API key to GitHub.

## 6. Run the application

```powershell
streamlit run app.py
```

Streamlit normally opens the app in your browser.

## Deploy on Render

1. Push the project to GitHub.
2. Log into Render.
3. Create a new Web Service.
4. Connect your GitHub repository.
5. Use:

Build Command:

```text
pip install -r requirements.txt
```

Start Command:

```text
streamlit run app.py --server.address 0.0.0.0 --server.port $PORT
```

6. Add environment variables in Render:

```text
OPENAI_API_KEY = your real key
OPENAI_MODEL = gpt-5.6
```

7. Deploy.

## Important

This project is designed for mock interviews and interview preparation.
It should not be used to secretly obtain answers during a live employer interview.
