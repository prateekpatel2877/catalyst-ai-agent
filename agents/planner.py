import json
import os
from groq import Groq
from dotenv import load_dotenv
from prompts.templates import LEARNING_PLAN_PROMPT

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_learning_plan(gap_result: dict) -> dict:
    """
    Generate a personalized learning plan based on gap analysis.
    
    Input: gap_result from gap_analyzer.analyze_gaps()
    Output: structured learning plan with resources and time estimates
    """

    strong_skills = gap_result.get("strong_skills", [])
    critical_gaps = gap_result.get("critical_gaps", [])
    moderate_gaps = gap_result.get("moderate_gaps", [])
    adjacent_skills = gap_result.get("adjacent_skills", [])

    # If no gaps found, return early
    if not critical_gaps and not moderate_gaps:
        return {
            "learning_plan": [],
            "total_estimated_weeks": 0,
            "recommended_approach": "The candidate appears well-suited for this role. Focus on staying updated with latest developments."
        }

    prompt = LEARNING_PLAN_PROMPT.format(
        strong_skills=json.dumps(strong_skills),
        critical_gaps=json.dumps(critical_gaps),
        moderate_gaps=json.dumps(moderate_gaps),
        adjacent_skills=json.dumps(adjacent_skills)
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an expert learning coach. Always return valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=2000
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"LLM returned invalid JSON for learning plan:\n{raw}")

    return result


def enrich_with_resources(learning_plan: dict, chroma_retriever) -> dict:
    """
    Enrich each skill in the learning plan with resources
    retrieved from ChromaDB.
    
    Input:
        learning_plan: output from generate_learning_plan()
        chroma_retriever: ChromaDB retriever instance
    
    Output:
        learning_plan with resources added to each skill
    """
    enriched_plan = learning_plan.copy()

    for item in enriched_plan.get("learning_plan", []):
        skill = item["skill"]

        # Query ChromaDB for relevant resources
        try:
            results = chroma_retriever.query(skill, n_results=3)
            item["resources"] = results
        except Exception:
            item["resources"] = []

    return enriched_plan


def format_learning_plan(learning_plan: dict) -> str:
    """
    Format learning plan as readable markdown for Streamlit display.
    """
    lines = []

    lines.append("## 🎯 Your Personalized Learning Plan\n")

    approach = learning_plan.get("recommended_approach", "")
    if approach:
        lines.append(f"**Strategy:** {approach}\n")

    total_weeks = learning_plan.get("total_estimated_weeks", 0)
    if total_weeks:
        lines.append(f"**Total Estimated Time:** {total_weeks} weeks\n")

    lines.append("---\n")

    for i, item in enumerate(learning_plan.get("learning_plan", []), 1):
        skill = item.get("skill", "")
        priority = item.get("priority", "").upper()
        weeks = item.get("estimated_weeks", "?")
        reason = item.get("reason", "")
        milestones = item.get("milestones", [])
        resources = item.get("resources", [])

        priority_emoji = "🔴" if priority == "HIGH" else "🟡"

        lines.append(f"### {i}. {skill} {priority_emoji} ({priority} PRIORITY)")
        lines.append(f"**Time Estimate:** {weeks} weeks")
        lines.append(f"**Why:** {reason}\n")

        if milestones:
            lines.append("**Milestones:**")
            for m in milestones:
                lines.append(f"- {m}")
            lines.append("")

        if resources:
            lines.append("**📚 Resources:**")
            for r in resources:
                title = r.get("title", "Resource")
                url = r.get("url", "#")
                rtype = r.get("type", "")
                lines.append(f"- [{title}]({url}) _{rtype}_")
            lines.append("")

        lines.append("---\n")

    return "\n".join(lines)