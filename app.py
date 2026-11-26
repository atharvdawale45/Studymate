
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
    st.write("Get suggestions for balancing a busy day, preparing for exams, or improving your current study plan.")
    question = st.text_area("Your question", placeholder="I have college from 9 to 4, gym at 6, and an exam on Friday. Help me make this realistic.")
    if st.button("Ask StudyMate AI", type="primary"):
        if not question.strip():
            st.warning("Write a question first.")
        else:
            with st.spinner("Your AI study coach is preparing an answer..."):
                try:
                    answer, retrieved, trace = run_multi_agent_workflow(question, saved_plan)
                    st.markdown('<div class="section-card">', unsafe_allow_html=True)
                    st.markdown(answer)
                    st.markdown('</div>', unsafe_allow_html=True)
                except Exception as exc:
                    st.warning(f"Could not run the AI workflow: {exc}")
                    st.caption("Check GEMINI_API_KEY, model access, internet connection and installed dependencies.")

st.divider()
st.caption("StudyMate AI · Personal study planning + AI-powered study support")
