def calculate_proficiency_score(evaluation_scores: list[dict]) -> float:
    """
    Calculate overall proficiency score for a skill
    based on multiple question evaluations.
    
    Each evaluation has:
    - score: 0-10
    - confidence: low / medium / high
    - difficulty: easy / medium / hard
    """
    if not evaluation_scores:
        return 0.0

    # Difficulty weights
    difficulty_weights = {
        "easy": 0.2,
        "medium": 0.5,
        "hard": 0.8
    }

    # Confidence multipliers
    confidence_multipliers = {
        "low": 0.7,
        "medium": 1.0,
        "high": 1.2
    }

    total_weight = 0
    weighted_sum = 0

    for eval in evaluation_scores:
        score = eval.get("score", 0)
        confidence = eval.get("confidence", "medium")
        difficulty = eval.get("difficulty", "medium")

        weight = difficulty_weights.get(difficulty, 0.5)
        multiplier = confidence_multipliers.get(confidence, 1.0)

        weighted_score = score * multiplier
        weighted_sum += weighted_score * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    raw_score = weighted_sum / total_weight

    # Normalize to 0-10
    final_score = min(round(raw_score, 2), 10.0)
    return final_score


def get_proficiency_label(score: float) -> str:
    """Convert numeric score to proficiency label."""
    if score >= 8.5:
        return "Expert"
    elif score >= 7.0:
        return "Proficient"
    elif score >= 5.5:
        return "Intermediate"
    elif score >= 3.5:
        return "Beginner"
    else:
        return "No Proficiency"


def get_score_color(score: float) -> str:
    """Return color code based on score for Streamlit UI."""
    if score >= 7.0:
        return "green"
    elif score >= 5.0:
        return "orange"
    else:
        return "red"


def determine_next_difficulty(current_difficulty: str, score: int) -> str:
    """
    Adaptive difficulty — adjust next question difficulty
    based on how well candidate answered current question.
    """
    if score >= 7:
        # Doing well, increase difficulty
        if current_difficulty == "easy":
            return "medium"
        elif current_difficulty == "medium":
            return "hard"
        else:
            return "hard"
    elif score <= 4:
        # Struggling, decrease difficulty
        if current_difficulty == "hard":
            return "medium"
        elif current_difficulty == "medium":
            return "easy"
        else:
            return "easy"
    else:
        # Average, keep same difficulty
        return current_difficulty


def summarize_assessment(skill_scores: dict) -> dict:
    """
    Summarize full assessment results across all skills.
    
    Input: {skill_name: [list of evaluation dicts]}
    Output: {skill_name: {score, label, color}}
    """
    summary = {}
    for skill, evaluations in skill_scores.items():
        score = calculate_proficiency_score(evaluations)
        summary[skill] = {
            "score": score,
            "label": get_proficiency_label(score),
            "color": get_score_color(score)
        }
    return summary