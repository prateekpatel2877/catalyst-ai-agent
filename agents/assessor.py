import json
import os
from groq import Groq
from dotenv import load_dotenv
from prompts.templates import QUESTION_GENERATION_PROMPT, ANSWER_EVALUATION_PROMPT
from utils.scoring import determine_next_difficulty

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_questions(skill: str, difficulty: str = "medium", 
                       num_questions: int = 1, question_type: str = "conceptual") -> dict:
    """
    Generate assessment questions for a given skill.
    """
    prompt = QUESTION_GENERATION_PROMPT.format(
        skill=skill,
        difficulty=difficulty,
        num_questions=num_questions,
        question_type=question_type
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a technical interviewer. Always return valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4,
        max_tokens=1000
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"LLM returned invalid JSON for question generation:\n{raw}")

    return result


def evaluate_answer(skill: str, question: str, answer: str, difficulty: str) -> dict:
    """
    Evaluate a candidate's answer using LLM as judge.
    Returns score, confidence, feedback, follow_up_needed.
    """
    prompt = ANSWER_EVALUATION_PROMPT.format(
        skill=skill,
        question=question,
        answer=answer,
        difficulty=difficulty
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a strict but fair technical evaluator. Always return valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=500
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"LLM returned invalid JSON for answer evaluation:\n{raw}")

    # Add difficulty to result for scoring
    result["difficulty"] = difficulty
    return result


def run_skill_assessment(skill: str, num_rounds: int = 3) -> list:
    """
    Run a full adaptive assessment for a single skill.
    Returns list of evaluation results.
    
    This is called per skill during the Streamlit conversational loop.
    """
    evaluations = []
    current_difficulty = "medium"
    question_types = ["conceptual", "practical", "scenario-based"]

    for i in range(num_rounds):
        question_type = question_types[i % len(question_types)]

        # Generate question
        question_data = generate_questions(
            skill=skill,
            difficulty=current_difficulty,
            num_questions=1,
            question_type=question_type
        )

        question_text = question_data["questions"][0]["question"]

        # Return question to Streamlit for display
        # Answer comes back from user input
        yield {
            "type": "question",
            "skill": skill,
            "question": question_text,
            "difficulty": current_difficulty,
            "round": i + 1,
            "total_rounds": num_rounds
        }

        # After yield, Streamlit sends back the answer
        # This generator pauses here — answer handling is in app.py

    return evaluations


def evaluate_single_answer(skill: str, question: str, 
                           answer: str, difficulty: str) -> dict:
    """
    Evaluate a single answer and return result.
    Used directly by Streamlit app.
    """
    evaluation = evaluate_answer(skill, question, answer, difficulty)
    next_difficulty = determine_next_difficulty(difficulty, evaluation["score"])
    evaluation["next_difficulty"] = next_difficulty
    return evaluation