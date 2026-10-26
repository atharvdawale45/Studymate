import json
import os
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
PROFILE_PATH = DATA / "profile.json"
ACTIVITY_PATH = DATA / "activities.json"
TASK_PATH = DATA / "tasks.json"
PLAN_PATH = DATA / "plan.json"

st.set_page_config(page_title="StudyMate AI", page_icon="✦", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: linear-gradient(135deg, #0b1020 0%, #111b32 45%, #101426 100%); color: #f4f7ff; }
[data-testid="stSidebar"] { background: #0a1020; border-right: 1px solid rgba(255,255,255,.08); }
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1450px; }
h1,h2,h3 { font-family: 'Manrope', sans-serif !important; letter-spacing: -.035em; color: #f7f8ff; }
p, label, span, div { }
.hero { padding: 1.6rem 1.8rem; border: 1px solid rgba(255,255,255,.12); border-radius: 24px; background: radial-gradient(circle at 85% 20%, rgba(125,93,255,.35), transparent 32%), linear-gradient(115deg, rgba(34,48,83,.96), rgba(18,27,49,.96)); box-shadow: 0 18px 60px rgba(0,0,0,.18); margin-bottom: 1.2rem; }
.eyebrow { color: #a9b7ff; text-transform: uppercase; font-size: .76rem; font-weight: 800; letter-spacing: .16em; }
.hero-title { font-family: 'Manrope',sans-serif; font-size: clamp(2rem,4vw,3.3rem); line-height: 1.1; font-weight: 800; margin: .45rem 0 .65rem; }
.hero-sub { color: #c6cee3; max-width: 780px; font-size: 1.03rem; line-height: 1.65; }
.metric-card { padding: 1rem 1.1rem; border-radius: 18px; background: rgba(255,255,255,.055); border: 1px solid rgba(255,255,255,.09); min-height: 112px; }
.metric-label { color: #aeb8d0; font-size: .82rem; font-weight: 600; }
.metric-value { color: #ffffff; font-family: 'Manrope',sans-serif; font-size: 1.8rem; font-weight: 800; margin-top: .35rem; }
.metric-note { color: #91e7d2; font-size: .76rem; margin-top: .2rem; }
.section-card { border-radius: 18px; border: 1px solid rgba(255,255,255,.09); padding: 1.1rem 1.25rem; background: rgba(255,255,255,.045); margin-bottom: .8rem; }
.small-muted { color: #aeb8d0; font-size: .9rem; }
.stButton > button, .stDownloadButton > button { border-radius: 12px; font-weight: 700; min-height: 2.7rem; border: 1px solid rgba(255,255,255,.12); }
.stButton > button[kind="primary"] { background: linear-gradient(95deg,#7865ff,#4c8dff); border: none; }
div[data-testid="stMetric"] { background: rgba(255,255,255,.055); border: 1px solid rgba(255,255,255,.09); padding: 14px 16px; border-radius: 16px; }
div[data-testid="stMetricLabel"] { color: #b8c2dc; }
div[data-testid="stMetricValue"] { color: #fff; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; background: rgba(255,255,255,.035); padding: 8px; border-radius: 15px; }
.stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 9px 14px; }
hr { border-color: rgba(255,255,255,.1); }
div[data-testid="stAlert"] { border-radius: 14px; }
</style>
""", unsafe_allow_html=True)

def load_json(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback
    except Exception:
        return fallback

def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")

def default_profile():
    return {
        "name": "", "wake": "06:30", "sleep": "23:00", "study_start": "17:00",
        "study_end": "22:00", "focus": 45, "break": 10, "daily_limit": 240,
        "study_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
        "energy": "Evening", "goal": "Prepare for exams", "style": "Practice questions",
        "commute_minutes": 60, "sleep_hours": 7.5
    }

profile = load_json(PROFILE_PATH, default_profile())
activities = load_json(ACTIVITY_PATH, [])
tasks = load_json(TASK_PATH, [])
saved_plan = load_json(PLAN_PATH, [])

def mins(hhmm):
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m

def hhmm(n):
    n = int(n) % 1440
    return f"{n // 60:02d}:{n % 60:02d}"

def fuzzy_score(task, today=None):
    today = today or date.today()
    try:
        days = (date.fromisoformat(task["due"]) - today).days
    except Exception:
        days = 7
    # Simple low/medium/high fuzzy urgency memberships.
    urgency_low = max(0, min(1, (days - 5) / 9))
    urgency_high = max(0, min(1, (7 - days) / 6))
    urgency_medium = max(0, 1 - abs(days - 4) / 4)
    urgency = min(1, .2 * urgency_low + .55 * urgency_medium + .95 * urgency_high)
    importance = (int(task.get("importance", 3)) - 1) / 4
    confidence_gap = (5 - int(task.get("confidence", 3))) / 4
    difficulty = (int(task.get("difficulty", 3)) - 1) / 4
    effort = min(1, int(task.get("remaining", task.get("estimate", 60))) / 300)
    return round(max(0, min(100, (0.38*urgency + 0.28*importance + 0.18*confidence_gap + 0.10*difficulty + 0.06*effort)*100)), 1)

def events_for(day):
    return [a for a in activities if a.get("date") == day.isoformat()]

def available_intervals(day, start, end):
    busy = []
    for item in events_for(day):
        try:
            a, b = mins(item["start"]), mins(item["end"])
            if a < end and b > start:
                busy.append((max(a, start), min(b, end)))
        except Exception:
            continue
    busy.sort()
    merged = []
    for a, b in busy:
        if not merged or a > merged[-1][1]:
            merged.append([a, b])
        else:
            merged[-1][1] = max(merged[-1][1], b)
    result, cursor = [], start
    for a, b in merged:
        if cursor < a:
            result.append((cursor, a))
        cursor = max(cursor, b)
    if cursor < end:
        result.append((cursor, end))
    return result

def generate_plan(horizon=7):
    today = date.today()
    active = [t.copy() for t in tasks if t.get("status", "Pending") != "Completed" and int(t.get("remaining", t.get("estimate", 0))) > 0]
    for t in active:
        t["_score"] = fuzzy_score(t, today)
    active.sort(key=lambda x: (x["_score"], x.get("due", "9999-12-31")), reverse=True)
    left = {t["id"]: int(t.get("remaining", t.get("estimate", 60))) for t in active}
    plan = []
    allowed = set(profile.get("study_days", []))
    start = mins(profile.get("study_start", "17:00"))
    end = mins(profile.get("study_end", "22:00"))
    if end <= start:
        start, end = 17*60, 22*60
    focus = int(profile.get("focus", 45))
    pause = int(profile.get("break", 10))
    limit = int(profile.get("daily_limit", 240))
    for offset in range(horizon):
        day = today + timedelta(days=offset)
        if day.strftime("%A") not in allowed:
            continue
        used = 0
        for a, b in available_intervals(day, start, end):
            cursor = a
            while cursor + 20 <= b and used < limit:
                possible = [t for t in active if left.get(t["id"], 0) > 0]
                if not possible:
                    break
                chosen = None
                duration = 0
                for t in possible:
                    candidate = min(focus, left[t["id"]], b-cursor, limit-used)
                    if candidate >= 20:
                        chosen, duration = t, candidate
                        break
                if chosen is None:
                    break
                finish = cursor + duration
                plan.append({
                    "date": day.isoformat(), "day": day.strftime("%A"), "start": hhmm(cursor),
                    "end": hhmm(finish), "title": chosen["title"], "subject": chosen["subject"],
                    "task_id": chosen["id"], "minutes": duration, "priority": chosen["_score"],
                    "why": "deadline / importance / confidence / difficulty score"
                })
                left[chosen["id"]] -= duration
                used += duration
                cursor = finish + pause
    return plan, left

def get_ai_reply(question, plan):
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return None, "AI coach is not configured yet. Add GEMINI_API_KEY to your .env file. The timetable planner works without it."
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key)
        context = [{"date": x["date"], "time": f'{x["start"]}-{x["end"]}', "task": x["title"], "subject": x["subject"]} for x in plan[:30]]
        prompt = (
            "You are StudyMate, a practical and kind student study coach. "
            "Give realistic advice based on the supplied schedule. Do not invent completed actions. "
            "Use short, natural language.\n\n"
            f"Student question: {question}\n"
            f"Schedule: {json.dumps(context)}\n"
            "Give a recommendation, risks, and one next step."
        )
        result = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.4),
        )
        return result.text, None
    except Exception as exc:
        return None, f"Could not contact Gemini: {exc}. Check the Gemini API key, model name, internet connection, and API access."

# Sidebar profile
with st.sidebar:
    st.markdown("## ✦ StudyMate AI")
    st.caption("YOUR PERSONAL STUDY COMMAND CENTRE")
    with st.form("profile"):
        st.markdown("### Your routine")
        name = st.text_input("Your name", profile.get("name", ""))
        wake = st.time_input("Wake-up time", time.fromisoformat(profile.get("wake", "06:30")))
        sleep = st.time_input("Bedtime", time.fromisoformat(profile.get("sleep", "23:00")))
        study_start = st.time_input("Preferred study start", time.fromisoformat(profile.get("study_start", "17:00")))
        study_end = st.time_input("Preferred study end", time.fromisoformat(profile.get("study_end", "22:00")))
        focus = st.select_slider("Focus session", options=[25, 30, 45, 50, 60, 75, 90], value=int(profile.get("focus", 45)))
        break_time = st.select_slider("Break length", options=[5, 10, 15, 20], value=int(profile.get("break", 10)))
        daily_limit = st.slider("Daily study cap (minutes)", 60, 600, int(profile.get("daily_limit", 240)), 30)
        days = st.multiselect("Study days", ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], default=profile.get("study_days", []))
        energy = st.selectbox("Best energy time", ["Morning", "Afternoon", "Evening", "Varies"], index=["Morning","Afternoon","Evening","Varies"].index(profile.get("energy", "Evening")))
        style = st.selectbox("Preferred learning style", ["Practice questions","Reading and notes","Flashcards","Videos and examples","Mixed"], index=["Practice questions","Reading and notes","Flashcards","Videos and examples","Mixed"].index(profile.get("style", "Practice questions")))
        goal = st.text_input("Main academic goal", profile.get("goal", "Prepare for exams"))
        commute = st.number_input("Daily commute (minutes)", 0, 300, int(profile.get("commute_minutes", 60)), 15)
        sleep_hours = st.slider("Target sleep (hours)", 5.0, 10.0, float(profile.get("sleep_hours", 7.5)), .5)
        save_profile = st.form_submit_button("Save my routine", type="primary", use_container_width=True)
    if save_profile:
        profile = {"name": name, "wake": wake.strftime("%H:%M"), "sleep": sleep.strftime("%H:%M"),
                   "study_start": study_start.strftime("%H:%M"), "study_end": study_end.strftime("%H:%M"),
                   "focus": focus, "break": break_time, "daily_limit": daily_limit, "study_days": days,
                   "energy": energy, "style": style, "goal": goal, "commute_minutes": commute, "sleep_hours": sleep_hours}
        save_json(PROFILE_PATH, profile)
        st.success("Routine saved!")
        st.rerun()

# Hero header
today = date.today()
greeting = "Good morning" if datetime.now().hour < 12 else ("Good afternoon" if datetime.now().hour < 17 else "Good evening")
display_name = profile.get("name", "").strip()
st.markdown(f"""
<div class="hero">
  <div class="eyebrow">✦ Your personal learning workspace</div>
  <div class="hero-title">{greeting}{', ' + display_name if display_name else ''}.</div>
  <div class="hero-sub">Build a study routine around your real life — classes, commute, meals, exercise, rest and deadlines. StudyMate turns your day into a plan you can actually follow.</div>
</div>
""", unsafe_allow_html=True)

active_tasks = [t for t in tasks if t.get("status") != "Completed"]
today_activities = events_for(today)
scheduled_today = [p for p in saved_plan if p.get("date") == today.isoformat()]
study_mins_today = sum(int(p.get("minutes", 0)) for p in scheduled_today)
activity_mins = sum(max(0, mins(a["end"])-mins(a["start"])) for a in today_activities if a.get("start") and a.get("end"))
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Active study tasks</div><div class="metric-value">{len(active_tasks)}</div><div class="metric-note">Keep the next step clear</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Activities today</div><div class="metric-value">{len(today_activities)}</div><div class="metric-note">Your day, not just study</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Planned study today</div><div class="metric-value">{study_mins_today // 60}h {study_mins_today % 60}m</div><div class="metric-note">From your latest plan</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Time already committed</div><div class="metric-value">{activity_mins // 60}h {activity_mins % 60}m</div><div class="metric-note">Activities entered for today</div></div>', unsafe_allow_html=True)

tabs = st.tabs(["🏠 Overview", "🧭 My whole day", "📚 Study tasks", "🗓️ Smart study plan", "✨ AI coach", "⚙️ About project"])

with tabs[0]:
    left, right = st.columns([1.4, 1])
    with left:
        st.markdown("### Your day at a glance")
        if today_activities:
            day_rows = [{"Time": f'{a["start"]}–{a["end"]}', "Activity": a["title"], "Type": a.get("category", "Other"), "Duration": f'{mins(a["end"])-mins(a["start"])} min'} for a in sorted(today_activities, key=lambda x:x["start"])]
            st.dataframe(pd.DataFrame(day_rows), use_container_width=True, hide_index=True)
        else:
            st.markdown('<div class="section-card"><b>Your day is still a blank canvas.</b><br><span class="small-muted">Add college, travel, meals, exercise, family time, work, hobbies and rest in “My whole day”.</span></div>', unsafe_allow_html=True)
    with right:
        st.markdown("### Quick start")
        st.markdown('<div class="section-card"><b>1 · Map your real day</b><br><span class="small-muted">Add recurring commitments and how long each activity takes.</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-card"><b>2 · Add academic tasks</b><br><span class="small-muted">Include deadlines, effort, difficulty and confidence.</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-card"><b>3 · Generate your plan</b><br><span class="small-muted">The planner fits study sessions around blocked time.</span></div>', unsafe_allow_html=True)
        st.markdown(f"**Main goal:** {profile.get('goal', 'Prepare for exams')}")
        st.markdown(f"**Preferred learning style:** {profile.get('style', 'Mixed')}")
    st.markdown("### Planning snapshot")
    if tasks:
        summary = []
        for t in tasks:
            summary.append({"Subject": t["subject"], "Task": t["title"], "Deadline": t["due"], "Priority": fuzzy_score(t), "Status": t.get("status", "Pending")})
        st.dataframe(pd.DataFrame(summary).sort_values("Priority", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Start by adding your daily activities and academic tasks. The planner uses both to build a realistic timetable.")

with tabs[1]:
    st.markdown("### 🧭 Tell StudyMate what your day looks like")
    st.write("Add everything that uses time: lectures, labs, commute, meals, gym, part-time work, chores, family time, hobbies, sleep or breaks. The planner will protect these blocks and schedule study around them.")
    with st.form("activity_form", clear_on_submit=True):
        a1, a2 = st.columns(2)
        activity_title = a1.text_input("Activity name", placeholder="e.g. College lectures")
        category = a2.selectbox("Category", ["College / Classes", "Commute", "Meals", "Exercise / Gym", "Work", "Family / Chores", "Hobby / Social", "Sleep / Rest", "Other"])
        a3, a4, a5 = st.columns(3)
        activity_date = a3.date_input("Date", value=today)
        activity_start = a4.time_input("Start time", time(9, 0), key="activity_start")
        activity_end = a5.time_input("End time", time(16, 0), key="activity_end")
        repeat = st.checkbox("Repeat this activity on the same weekday for the next 7 days")
        activity_note = st.text_input("Notes (optional)", placeholder="e.g. includes lunch break")
        add_activity = st.form_submit_button("＋ Add activity", type="primary")
    if add_activity:
        if not activity_title.strip():
            st.error("Please give this activity a name.")
        elif activity_end <= activity_start:
            st.error("End time must be later than start time. For overnight activities, split the activity across two dates.")
        else:
            next_id = max([int(a.get("id",0)) for a in activities], default=0) + 1
            dates = [activity_date]
            if repeat:
                dates += [activity_date + timedelta(days=i) for i in range(1, 8) if (activity_date + timedelta(days=i)).strftime("%A") == activity_date.strftime("%A")]
            for d in dates:
                activities.append({"id": next_id, "title": activity_title.strip(), "category": category, "date": d.isoformat(),
                                   "start": activity_start.strftime("%H:%M"), "end": activity_end.strftime("%H:%M"), "notes": activity_note})
                next_id += 1
            save_json(ACTIVITY_PATH, activities)
            st.success("Activity added to your day.")
            st.rerun()
    if activities:
        st.markdown("#### Saved activities")
        filter_date = st.date_input("Show activities for", value=today, key="filter_activities")
        shown = sorted(events_for(filter_date), key=lambda x:x["start"])
        if shown:
            rows = [{"ID": a["id"], "Time": f'{a["start"]}–{a["end"]}', "Activity": a["title"], "Category": a.get("category","Other"),
                     "Duration": f'{mins(a["end"])-mins(a["start"])} min', "Notes": a.get("notes","")} for a in shown]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.caption("No activities entered for this date.")
        with st.form("delete_activity_form"):
            del_activity_id = st.selectbox("Remove an activity", [a["id"] for a in activities],
                                           format_func=lambda x: next((f'{a["date"]} · {a["start"]} · {a["title"]}' for a in activities if a["id"] == x), str(x)))
            remove_activity = st.form_submit_button("Remove selected activity")
        if remove_activity:
            activities = [a for a in activities if a["id"] != del_activity_id]
            save_json(ACTIVITY_PATH, activities)
            st.rerun()
    else:
        st.info("No activities yet. Add a full-day routine so the study plan reflects your actual availability.")

with tabs[2]:
    st.markdown("### 📚 Build your academic workload")
    with st.form("task_form", clear_on_submit=True):
        t1, t2 = st.columns(2)
        task_title = t1.text_input("Task / topic", placeholder="e.g. Revise SVM and decision trees")
        subject = t2.text_input("Subject", placeholder="e.g. Machine Learning")
        t3, t4, t5 = st.columns(3)
        due = t3.date_input("Deadline / exam date", value=today + timedelta(days=5))
        estimate = t4.number_input("Total study time needed (minutes)", min_value=20, max_value=5000, value=120, step=20)
        importance = t5.slider("Importance", 1, 5, 4)
        t6, t7 = st.columns(2)
        difficulty = t6.slider("Difficulty", 1, 5, 3)
        confidence = t7.slider("Your confidence", 1, 5, 3, help="1 means I need lots of help; 5 means I feel confident.")
        task_notes = st.text_area("Topics / instructions", placeholder="Chapters, questions, practicals, or assignment details")
        add_task = st.form_submit_button("＋ Add study task", type="primary")
    if add_task:
        if not task_title.strip() or not subject.strip():
            st.error("Enter both the task name and subject.")
        else:
            next_id = max([int(t.get("id",0)) for t in tasks], default=0) + 1
            tasks.append({"id": next_id, "title": task_title.strip(), "subject": subject.strip(), "due": due.isoformat(),
                          "estimate": int(estimate), "remaining": int(estimate), "importance": importance,
                          "difficulty": difficulty, "confidence": confidence, "notes": task_notes, "status": "Pending"})
            save_json(TASK_PATH, tasks)
            st.success("Study task added.")
            st.rerun()
    if tasks:
        rows = [{"ID": t["id"], "Subject": t["subject"], "Task": t["title"], "Deadline": t["due"],
                 "Remaining (min)": t.get("remaining",t.get("estimate",0)), "Priority / 100": fuzzy_score(t), "Status": t.get("status","Pending")} for t in tasks]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        with st.form("update_task"):
            selected_id = st.selectbox("Choose task to update", [t["id"] for t in tasks],
                                       format_func=lambda x: next((f'{t["subject"]} — {t["title"]}' for t in tasks if t["id"] == x), str(x)))
            selected = next(t for t in tasks if t["id"] == selected_id)
            new_remaining = st.number_input("Remaining study minutes", 0, 5000, int(selected.get("remaining", selected.get("estimate", 60))), 20)
            new_status = st.selectbox("Progress", ["Pending", "In progress", "Completed"], index=["Pending","In progress","Completed"].index(selected.get("status","Pending")))
            update = st.form_submit_button("Save task progress")
        if update:
            for t in tasks:
                if t["id"] == selected_id:
                    t["remaining"] = 0 if new_status == "Completed" else int(new_remaining)
                    t["status"] = new_status
            save_json(TASK_PATH, tasks)
            st.success("Progress updated. Regenerate your study plan.")
            st.rerun()
        with st.form("delete_task"):
            del_task_id = st.selectbox("Task to delete", [t["id"] for t in tasks],
                                       format_func=lambda x: next((f'{t["subject"]} — {t["title"]}' for t in tasks if t["id"] == x), str(x)))
            delete_task = st.form_submit_button("Delete selected task")
        if delete_task:
            tasks = [t for t in tasks if t["id"] != del_task_id]
            save_json(TASK_PATH, tasks)
            st.rerun()
    else:
        st.info("Add subjects, exams, assignments, practicals and revision topics here.")

with tabs[3]:
    st.markdown("### 🗓️ Your personalised study plan")
    st.write("StudyMate ranks tasks using fuzzy-style priority scoring, blocks out your activities, then fits focus sessions into the time left.")
    if st.button("✦ Generate my study plan", type="primary", use_container_width=False):
        plan, leftover = generate_plan()
        saved_plan = plan
        save_json(PLAN_PATH, saved_plan)
        save_json(DATA / "unscheduled.json", leftover)
        st.session_state["leftover"] = leftover
        st.success("Your plan has been generated.")
    if saved_plan:
        total = sum(int(p["minutes"]) for p in saved_plan)
        k1,k2,k3 = st.columns(3)
        k1.metric("Study sessions", len(saved_plan))
        k2.metric("Total planned time", f"{total//60}h {total%60}m")
        k3.metric("Tasks scheduled", len(set(p["task_id"] for p in saved_plan)))
        date_choice = st.date_input("View plan for date", value=today, key="plan_date")
        day_plan = [p for p in saved_plan if p["date"] == date_choice.isoformat()]
        if day_plan:
            st.dataframe(pd.DataFrame([{"Time": f'{p["start"]}–{p["end"]}', "Subject": p["subject"], "Study session": p["title"],
                                        "Duration": f'{p["minutes"]} min', "Priority": p["priority"], "Reason": p["why"]} for p in day_plan]),
                         use_container_width=True, hide_index=True)
        else:
            st.info("No study sessions on this date. Check your available days and time window.")
        st.markdown("#### Full 7-day plan")
        plan_df = pd.DataFrame([{"Date": p["date"], "Day": p["day"], "Start": p["start"], "End": p["end"],
                                 "Subject": p["subject"], "Task": p["title"], "Minutes": p["minutes"], "Priority": p["priority"]} for p in saved_plan])
        st.dataframe(plan_df, use_container_width=True, hide_index=True)
        st.download_button("⬇ Download timetable (CSV)", plan_df.to_csv(index=False).encode("utf-8"), "studymate_weekly_plan.csv", "text/csv")
        leftover = st.session_state.get("leftover", load_json(DATA / "unscheduled.json", {}))
        if leftover:
            task_map = {t["id"]: t for t in tasks}
            not_fit = [(task_map.get(int(k)), v) for k,v in leftover.items() if int(v)>0]
            if not_fit:
                st.markdown("#### Work that still needs time")
                for task, remaining in not_fit:
                    if task:
                        st.warning(f'**{task["title"]}** — {remaining} minutes remain unscheduled. Add more available time, another study day, or reduce the workload.')
        with st.expander("Record a completed study session"):
            choices = list(range(len(saved_plan)))
            session_index = st.selectbox("Completed session", choices, format_func=lambda i: f'{saved_plan[i]["date"]} {saved_plan[i]["start"]} · {saved_plan[i]["title"]}')
            if st.button("Mark session complete"):
                p = saved_plan[session_index]
                for t in tasks:
                    if t["id"] == p["task_id"]:
                        t["remaining"] = max(0, int(t.get("remaining",t.get("estimate",0))) - int(p["minutes"]))
                        t["status"] = "Completed" if t["remaining"] == 0 else "In progress"
                save_json(TASK_PATH, tasks)
                st.success("Progress saved. Generate a new plan to update future sessions.")
                st.rerun()
    else:
        st.markdown('<div class="section-card"><b>Your plan will appear here.</b><br><span class="small-muted">For the best result, first enter your routine, full-day activities and academic tasks.</span></div>', unsafe_allow_html=True)

with tabs[4]:
    st.markdown("### ✨ Ask your AI study coach")
    st.write("Get suggestions for balancing a busy day, preparing for exams, or reviewing your current study plan.")
    question = st.text_area("Your question", placeholder="I have college from 9 to 4, gym at 6, and an exam on Friday. Help me make this realistic.")
    if st.button("Ask StudyMate AI", type="primary"):
        if not question.strip():
            st.warning("Write a question first.")
        else:
            answer, error = get_ai_reply(question, saved_plan)
            if answer:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown(answer)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning(error)
                st.caption("Configure GEMINI_API_KEY in .env and restart the app to enable the AI coach.")

with tabs[5]:
    st.markdown("### ⚙️ Project overview")
    st.markdown("""
**StudyMate AI** is a student planning prototype combining:
- **Personal schedule capture:** classes, travel, meals, exercise, work, chores, social activities and rest.
- **Fuzzy-style decision support:** estimates task priority using urgency, importance, difficulty, confidence and remaining effort.
- **Planning workflow:** schedules focus sessions around entered activities and a daily study cap.
- **Progress tracking:** completed sessions reduce the remaining task workload.
- **Generative AI coach:** optional API-based study suggestions.

**Responsible use:** The timetable is a recommendation, not a command. Review it for travel time, meals, rest and your actual energy. The planner only knows activities you enter. Data is saved locally in the project's `data` folder. When you use the AI coach, your question and a short timetable summary are sent to the configured model provider. Do not enter sensitive information.
""")
    st.markdown("#### API configuration")
    st.code("GEMINI_API_KEY=your_gemini_api_key_here\nGEMINI_MODEL=gemini-2.5-flash", language="dotenv")
    st.caption("Put these settings in a local .env file. Never publish your API key.")

st.divider()
st.caption("StudyMate AI · Generative AI + planning workflow + fuzzy-style prioritisation · Student project prototype")
