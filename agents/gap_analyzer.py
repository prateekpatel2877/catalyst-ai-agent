import json
import os
from groq import Groq
from dotenv import load_dotenv
from prompts.templates import GAP_ANALYSIS_PROMPT
from utils.scoring import summarize_assessment

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def analyze_gaps(skill_scores: dict, required_skills: list) -> dict:
    """
    Analyze skill gaps based on assessment results.
    
    Input:
        skill_scores: {skill_name: [list of evaluation dicts]}
        required_skills: list of skills required by JD
    
    Output:
        gap analysis with critical gaps, moderate gaps, strong skills, adjacent skills
    """

    # First summarize raw scores
    summary = summarize_assessment(skill_scores)

    # Format assessment results for prompt
    assessment_results = []
    for skill, data in summary.items():
        assessment_results.append({
            "skill": skill,
            "score": data["score"],
            "proficiency": data["label"]
        })

    prompt = GAP_ANALYSIS_PROMPT.format(
        assessment_results=json.dumps(assessment_results, indent=2),
        required_skills=json.dumps(required_skills, indent=2)
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a career coach and skill gap analyst. Always return valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=1500
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        gap_result = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"LLM returned invalid JSON for gap analysis:\n{raw}")

    # Attach score summary to result
    gap_result["score_summary"] = summary

    return gap_result


def get_gap_priority_order(gap_result: dict) -> list:
    """
    Returns skills to learn in priority order.
    Critical gaps first, then moderate gaps.
    """
    priority_list = []

    for skill in gap_result.get("critical_gaps", []):
        priority_list.append({
            "skill": skill,
            "priority": "critical",
            "score": gap_result["score_summary"].get(skill, {}).get("score", 0)
        })

    for skill in gap_result.get("moderate_gaps", []):
        priority_list.append({
            "skill": skill,
            "priority": "moderate",
            "score": gap_result["score_summary"].get(skill, {}).get("score", 0)
        })

    return priority_list


def format_gap_summary(gap_result: dict) -> str:
    """
    Returns a human readable gap summary string for display in Streamlit.
    """
    lines = []

    lines.append("### 📊 Assessment Summary\n")

    if gap_result.get("strong_skills"):
        lines.append("**✅ Strong Skills:**")
        for skill in gap_result["strong_skills"]:
            score = gap_result["score_summary"].get(skill, {}).get("score", "N/A")
            label = gap_result["score_summary"].get(skill, {}).get("label", "")
            lines.append(f"- {skill}: {score}/10 ({label})")

    lines.append("")

    if gap_result.get("moderate_gaps"):
        lines.append("**⚠️ Skills to Improve:**")
        for skill in gap_result["moderate_gaps"]:
            score = gap_result["score_summary"].get(skill, {}).get("score", "N/A")
            label = gap_result["score_summary"].get(skill, {}).get("label", "")
            lines.append(f"- {skill}: {score}/10 ({label})")

    lines.append("")

    if gap_result.get("critical_gaps"):
        lines.append("**❌ Critical Gaps (Must Learn):**")
        for skill in gap_result["critical_gaps"]:
            score = gap_result["score_summary"].get(skill, {}).get("score", "N/A")
            label = gap_result["score_summary"].get(skill, {}).get("label", "")
            lines.append(f"- {skill}: {score}/10 ({label})")

    lines.append("")

    if gap_result.get("adjacent_skills"):
        lines.append("**🔗 Adjacent Skills (Easy Wins):**")
        for adj in gap_result["adjacent_skills"]:
            lines.append(f"- Learn **{adj['gap_skill']}** via your strength in "
                        f"**{adj['adjacent_to']}** — {adj['reason']}")

    return "\n".join(lines)