import json
import os
from groq import Groq
from dotenv import load_dotenv
from prompts.templates import SKILL_EXTRACTION_PROMPT

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def extract_skills(jd_text: str, resume_text: str) -> dict:
    """
    Extract required skills from JD and claimed skills from resume.
    Returns a structured skill matrix.
    """
    prompt = SKILL_EXTRACTION_PROMPT.format(
        jd_text=jd_text,
        resume_text=resume_text
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a precise skill extraction engine. Always return valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=2000
    )

    raw = response.choices[0].message.content.strip()

    # Clean up any accidental markdown
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"LLM returned invalid JSON:\n{raw}")

    # Validate structure
    required_keys = ["required_skills", "candidate_skills", "skill_matrix"]
    for key in required_keys:
        if key not in result:
            raise ValueError(f"Missing key in skill extraction result: {key}")

    return result


def get_skills_to_assess(skill_matrix: dict) -> list:
    """
    Returns list of required skills to assess.
    Prioritizes skills the candidate claims to have,
    but also includes skills they don't claim (to verify gaps).
    """
    all_skills = list(skill_matrix.keys())

    # Skills candidate claims — assess to verify
    claimed = [s for s, claimed in skill_matrix.items() if claimed]

    # Skills candidate doesn't claim — assess to find true gap
    not_claimed = [s for s, claimed in skill_matrix.items() if not claimed]

    # Assess all claimed skills first, then unclaimed
    return claimed + not_claimed


def display_skill_matrix(skill_extraction_result: dict) -> None:
    """
    Print skill matrix summary to console (for debugging).
    """
    print("\n=== SKILL MATRIX ===")
    print(f"Required Skills: {skill_extraction_result['required_skills']}")
    print(f"Candidate Claims: {skill_extraction_result['candidate_skills']}")
    print("\nSkill Coverage:")
    for skill, has_it in skill_extraction_result['skill_matrix'].items():
        status = "✓ Claimed" if has_it else "✗ Not claimed"
        print(f"  {skill}: {status}")