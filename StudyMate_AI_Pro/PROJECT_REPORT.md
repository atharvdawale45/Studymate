# StudyMate AI — Adaptive Student Study Planner

## Introduction
StudyMate AI is a student-focused planning application that turns a student's daily routine and academic workload into a personalised weekly study timetable. Instead of assuming that a student is free after college, it asks about classes, travel, meals, exercise, work, family responsibilities, hobbies and rest.

## Objectives
- Capture a student's routine, preferences and available study periods.
- Record time-consuming activities with dates, start times, end times and categories.
- Manage academic tasks with deadlines, estimated effort, importance, difficulty and confidence.
- Use fuzzy-style prioritisation to rank tasks.
- Place study sessions around entered activities.
- Update task progress and regenerate the timetable.
- Provide optional generative AI coaching through an API.

## Technologies
Python, Streamlit, Pandas, JSON local storage, python-dotenv and the OpenAI Python SDK.

## Methodology
The student first saves their routine and preferred study window. They then enter activities such as college, commute, meals, gym, work and rest. Academic tasks are added with a subject, deadline, estimated minutes, importance, difficulty and confidence rating.

A fuzzy-style priority function combines deadline urgency, importance, confidence, difficulty and remaining effort into a score from 0 to 100. A planning routine ranks pending tasks and places focus sessions into available time intervals, respecting fixed activities, preferred session length, breaks and a daily study cap. When a student records a completed session, the remaining time for that task is reduced and the timetable can be regenerated.

The optional AI coach responds to student questions and reviews a compact timetable summary. It provides advice, while the student remains responsible for deciding what changes to make.

## Agentic workflow
The project demonstrates a supervised planning workflow: collect state, prioritise work, generate a schedule, record progress, and regenerate after changes. The AI coach is a supporting generative component rather than an unrestricted autonomous agent.

## Limitations and future scope
The prototype relies on activities entered by the student and does not automatically read a college calendar. Its fuzzy-style score is a transparent heuristic rather than a validated formal fuzzy inference system. Future work could add calendar integration, reminders, energy-aware planning, recurring weekly events, formal Mamdani rules and analytics for planned versus completed study time.

## Conclusion
StudyMate AI combines an interactive dashboard, full-day activity capture, fuzzy-style task prioritisation, an adaptive timetable workflow and optional generative AI coaching. It aims to make a study plan more realistic by considering the student's whole day, not only academic tasks.
