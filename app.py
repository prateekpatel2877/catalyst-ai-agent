import streamlit as st
import os
from dotenv import load_dotenv
from utils.resume_parser import parse_resume
from utils.chroma_store import initialize_resource_store, query_resources
from agents.skill_extractor import extract_skills, get_skills_to_assess
from agents.assessor import generate_questions, evaluate_single_answer
from agents.gap_analyzer import analyze_gaps, format_gap_summary
from agents.planner import generate_learning_plan, enrich_with_resources, format_learning_plan

load_dotenv()

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Catalyst - AI Skill Assessor",
    page_icon="🧠",
    layout="wide"
)

# ─── Session State Init ────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "stage": "upload",           # upload → extracting → assessing → results
        "resume_text": "",
        "jd_text": "",
        "skill_extraction": {},
        "skills_to_assess": [],
        "current_skill_index": 0,
        "current_round": 0,
        "current_question": None,
        "current_difficulty": "medium",
        "skill_scores": {},          # {skill: [eval dicts]}
        "gap_result": {},
        "learning_plan": {},
        "chroma_collection": None,
        "chat_history": [],          # [{role, content}]
        "total_rounds_per_skill": 3
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session()

# ─── Header ───────────────────────────────────────────────────────────────────
st.title("🧠 Catalyst — AI Skill Assessment Agent")
st.caption("Upload your resume and a job description. The agent will assess your real proficiency and build a personalized learning plan.")
st.divider()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📋 Session Info")
    st.write(f"**Stage:** `{st.session_state.stage}`")

    if st.session_state.skills_to_assess:
        total = len(st.session_state.skills_to_assess)
        current = st.session_state.current_skill_index
        st.write(f"**Skills:** {min(current+1, total)} / {total}")
        st.progress(min(current / total, 1.0))

    if st.session_state.skill_scores:
        st.write("**Scores So Far:**")
        for skill, evals in st.session_state.skill_scores.items():
            if evals:
                avg = sum(e["score"] for e in evals) / len(evals)
                st.write(f"- {skill}: `{avg:.1f}/10`")

    if st.button("🔄 Start Over"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ─── Stage 1: Upload ──────────────────────────────────────────────────────────
if st.session_state.stage == "upload":
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 Upload Resume")
        resume_file = st.file_uploader(
            "Upload your resume",
            type=["pdf", "docx"],
            help="Supports PDF and DOCX formats"
        )

    with col2:
        st.subheader("📝 Paste Job Description")
        jd_text = st.text_area(
            "Paste the job description here",
            height=300,
            placeholder="Paste the full job description here..."
        )

    st.divider()

    if st.button("🚀 Start Assessment", type="primary", use_container_width=True):
        if not resume_file:
            st.error("Please upload your resume.")
        elif not jd_text.strip():
            st.error("Please paste the job description.")
        else:
            with st.spinner("Parsing resume..."):
                try:
                    resume_text = parse_resume(resume_file)
                    st.session_state.resume_text = resume_text
                    st.session_state.jd_text = jd_text
                except Exception as e:
                    st.error(f"Failed to parse resume: {e}")
                    st.stop()

            with st.spinner("Initializing knowledge base..."):
                try:
                    collection = initialize_resource_store()
                    st.session_state.chroma_collection = collection
                except Exception as e:
                    st.warning(f"ChromaDB init warning: {e}")

            with st.spinner("Extracting skills from JD and Resume..."):
                try:
                    skill_extraction = extract_skills(
                        st.session_state.jd_text,
                        st.session_state.resume_text
                    )
                    st.session_state.skill_extraction = skill_extraction
                    skills_to_assess = get_skills_to_assess(
                        skill_extraction["skill_matrix"]
                    )
                    st.session_state.skills_to_assess = skills_to_assess

                    # Initialize score tracker
                    for skill in skills_to_assess:
                        st.session_state.skill_scores[skill] = []

                except Exception as e:
                    st.error(f"Skill extraction failed: {e}")
                    st.stop()

            st.session_state.stage = "assessing"
            st.rerun()

# ─── Stage 2: Assessment ──────────────────────────────────────────────────────
elif st.session_state.stage == "assessing":
    skills = st.session_state.skills_to_assess
    idx = st.session_state.current_skill_index
    rounds = st.session_state.total_rounds_per_skill

    # Check if all skills done
    if idx >= len(skills):
        st.session_state.stage = "analyzing"
        st.rerun()

    current_skill = skills[idx]
    current_round = st.session_state.current_round

    st.subheader(f"🎯 Assessing: **{current_skill}**")
    st.caption(f"Skill {idx+1} of {len(skills)} · Round {current_round+1} of {rounds}")
    st.progress((current_round) / rounds)

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Generate question if not already generated
    if st.session_state.current_question is None:
        with st.spinner(f"Generating question for {current_skill}..."):
            try:
                question_types = ["conceptual", "practical", "scenario-based"]
                q_type = question_types[current_round % len(question_types)]

                question_data = generate_questions(
                    skill=current_skill,
                    difficulty=st.session_state.current_difficulty,
                    num_questions=1,
                    question_type=q_type
                )
                question_text = question_data["questions"][0]["question"]
                st.session_state.current_question = question_text

                # Add to chat history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"**Round {current_round+1} · {q_type.title()} · {st.session_state.current_difficulty.title()} difficulty**\n\n{question_text}"
                })
                st.rerun()

            except Exception as e:
                st.error(f"Failed to generate question: {e}")
                st.stop()

    # User answer input
    answer = st.chat_input("Type your answer here...")

    if answer:
        # Add user answer to chat
        st.session_state.chat_history.append({
            "role": "user",
            "content": answer
        })

        # Evaluate answer
        with st.spinner("Evaluating your answer..."):
            try:
                evaluation = evaluate_single_answer(
                    skill=current_skill,
                    question=st.session_state.current_question,
                    answer=answer,
                    difficulty=st.session_state.current_difficulty
                )

                # Store evaluation
                evaluation["round"] = current_round + 1
                st.session_state.skill_scores[current_skill].append(evaluation)

                # Update difficulty for next round
                st.session_state.current_difficulty = evaluation["next_difficulty"]

                # Show feedback
                score = evaluation["score"]
                feedback = evaluation["feedback"]

                if score >= 7:
                    emoji = "✅"
                elif score >= 4:
                    emoji = "⚠️"
                else:
                    emoji = "❌"

                feedback_msg = f"{emoji} **Score: {score}/10**\n\n{feedback}"
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": feedback_msg
                })

                # Move to next round or next skill
                next_round = current_round + 1
                if next_round >= rounds:
                    # Done with this skill
                    avg = sum(e["score"] for e in st.session_state.skill_scores[current_skill]) / rounds
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"✅ **{current_skill} assessment complete!** Average score: **{avg:.1f}/10**\n\nMoving to next skill..."
                    })
                    st.session_state.current_skill_index += 1
                    st.session_state.current_round = 0
                    st.session_state.current_question = None
                    st.session_state.current_difficulty = "medium"
                else:
                    st.session_state.current_round = next_round
                    st.session_state.current_question = None

                st.rerun()

            except Exception as e:
                st.error(f"Evaluation failed: {e}")
                st.stop()

# ─── Stage 3: Analyzing ───────────────────────────────────────────────────────
elif st.session_state.stage == "analyzing":
    st.subheader("🔍 Analyzing Results...")

    with st.spinner("Running gap analysis..."):
        try:
            gap_result = analyze_gaps(
                st.session_state.skill_scores,
                st.session_state.skill_extraction["required_skills"]
            )
            st.session_state.gap_result = gap_result
        except Exception as e:
            st.error(f"Gap analysis failed: {e}")
            st.stop()

    with st.spinner("Generating personalized learning plan..."):
        try:
            learning_plan = generate_learning_plan(gap_result)

            # Enrich with ChromaDB resources
            enriched_plan = enrich_with_resources(
                learning_plan,
                type("Retriever", (), {
                    "query": lambda self, skill, n_results=3: query_resources(skill, n_results)
                })()
            )
            st.session_state.learning_plan = enriched_plan
        except Exception as e:
            st.error(f"Learning plan generation failed: {e}")
            st.stop()

    st.session_state.stage = "results"
    st.rerun()

# ─── Stage 4: Results ─────────────────────────────────────────────────────────
elif st.session_state.stage == "results":
    st.subheader("📊 Assessment Results")

    tab1, tab2, tab3 = st.tabs(["Skill Scores", "Gap Analysis", "Learning Plan"])

    with tab1:
        st.markdown("### 🎯 Your Skill Scores")
        cols = st.columns(3)
        for i, (skill, evals) in enumerate(st.session_state.skill_scores.items()):
            if evals:
                avg = sum(e["score"] for e in evals) / len(evals)
                col = cols[i % 3]
                with col:
                    if avg >= 7:
                        st.success(f"**{skill}**\n\n{avg:.1f}/10")
                    elif avg >= 4:
                        st.warning(f"**{skill}**\n\n{avg:.1f}/10")
                    else:
                        st.error(f"**{skill}**\n\n{avg:.1f}/10")

    with tab2:
        gap_summary = format_gap_summary(st.session_state.gap_result)
        st.markdown(gap_summary)

    with tab3:
        plan_text = format_learning_plan(st.session_state.learning_plan)
        st.markdown(plan_text)

    st.divider()
    if st.button("🔄 Start New Assessment", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()