# StudyMate AI — Student Study Planner

## Run it easily in VS Code (Windows)

1. Download and extract this folder.
2. Open the folder in VS Code.
3. Choose **Terminal → New Terminal**.
4. Run these commands one at a time:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

These commands use the virtual environment directly, so activating it is optional. If `py` is not recognised, install Python 3.10+ from python.org and select **Add Python to PATH** during setup.

5. A browser page should open. If not, click the `http://localhost:8501` address printed in the terminal.
6. Optional: copy `.env.example` to `.env`, paste your API key, save, and restart Streamlit. The timetable works without an API key; the AI coach needs one.

## What to enter first
- Save your daily routine in the left sidebar.
- Open **My whole day** and add college, commute, meals, gym, work, chores, hobbies and other time blocks.
- Open **Study tasks** and add exams, assignments, practicals and revision topics.
- Open **Smart study plan** and click **Generate my study plan**.

## Included
- Attractive dark dashboard
- Daily routine and study preferences
- Activity planner with dates, start/end times, categories and duration
- Optional repeat-on-same-weekday activity for the next week
- Academic task manager
- Fuzzy-style priority scoring
- Weekly study-plan generation around entered activities
- Progress updates and CSV export
- Optional Google Gemini API study coach

## Notes
The app saves data locally in `data/`. The planner can only avoid activities that have been entered. For an overnight activity, add two separate blocks on two dates. This is a student project prototype, so review its timetable before relying on it.


## Configure Google Gemini
1. Copy `.env.example` to a new file named `.env` in this project folder.
2. Replace `YOUR_GEMINI_API_KEY_HERE` with your real Gemini API key.
3. Save the file and restart Streamlit.
4. Open the **AI coach** tab and ask a question.

Keep `.env` private. Do not commit it to GitHub. The timetable works even without a Gemini key.
