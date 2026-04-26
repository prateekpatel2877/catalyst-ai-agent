SKILL_EXTRACTION_PROMPT = """
You are an expert technical recruiter and skill analyzer.

Given a Job Description and a Resume, extract the following in JSON format:

1. required_skills: List of skills explicitly or implicitly required in the JD
2. candidate_skills: List of skills the candidate claims in their resume
3. skill_matrix: For each required skill, whether the candidate claims it (true/false)

Return ONLY valid JSON, no explanation, no markdown, no backticks.

Format:
{{
    "required_skills": ["skill1", "skill2", ...],
    "candidate_skills": ["skill1", "skill2", ...],
    "skill_matrix": {{
        "skill1": true,
        "skill2": false,
        ...
    }}
}}

Job Description:
{jd_text}

Resume:
{resume_text}
"""

QUESTION_GENERATION_PROMPT = """
You are a strict but fair technical interviewer assessing a candidate's real proficiency.

Generate {num_questions} questions to assess the candidate's knowledge of: {skill}

Difficulty level: {difficulty}  (easy / medium / hard)
Question type: {question_type}  (conceptual / practical / scenario-based)

Rules:
- Questions must be specific, not vague
- Each question should reveal real understanding, not just definitions
- Return ONLY valid JSON, no explanation, no markdown, no backticks

Format:
{{
    "skill": "{skill}",
    "difficulty": "{difficulty}",
    "questions": [
        {{
            "id": 1,
            "question": "...",
            "type": "{question_type}"
        }},
        ...
    ]
}}
"""

ANSWER_EVALUATION_PROMPT = """
You are an expert evaluator assessing a candidate's answer to a technical question.

Skill being assessed: {skill}
Question asked: {question}
Candidate's answer: {answer}
Difficulty level: {difficulty}

Evaluate the answer and return ONLY valid JSON, no explanation, no markdown, no backticks.

Format:
{{
    "score": <integer from 0 to 10>,
    "confidence": <"low" | "medium" | "high">,
    "feedback": "<one line feedback>",
    "follow_up_needed": <true | false>
}}

Scoring guide:
0-3: Wrong or very incomplete
4-6: Partially correct, missing key concepts
7-8: Correct with minor gaps
9-10: Excellent, shows deep understanding
"""

GAP_ANALYSIS_PROMPT = """
You are a career coach and learning path expert.

Based on the skill assessment results below, identify:
1. Critical gaps (score < 5) — must learn before applying
2. Moderate gaps (score 5-6) — should improve
3. Strong skills (score >= 7) — leverage these

Also identify adjacent skills — skills the candidate can learn easily given their existing strengths.

Assessment Results:
{assessment_results}

Required Skills for the role:
{required_skills}

Return ONLY valid JSON, no explanation, no markdown, no backticks.

Format:
{{
    "critical_gaps": ["skill1", "skill2"],
    "moderate_gaps": ["skill3"],
    "strong_skills": ["skill4", "skill5"],
    "adjacent_skills": [
        {{
            "gap_skill": "skill1",
            "adjacent_to": "existing_strong_skill",
            "reason": "why this is achievable"
        }}
    ]
}}
"""

LEARNING_PLAN_PROMPT = """
You are an expert learning coach creating a personalized upskilling plan.

Candidate's strong skills: {strong_skills}
Skills to learn (critical gaps): {critical_gaps}
Skills to improve (moderate gaps): {moderate_gaps}
Adjacent skill opportunities: {adjacent_skills}

Create a realistic, ordered learning plan. Prioritize adjacent skills first since they build on existing knowledge.

Return ONLY valid JSON, no explanation, no markdown, no backticks.

Format:
{{
    "learning_plan": [
        {{
            "skill": "skill_name",
            "priority": "high/medium",
            "estimated_weeks": <number>,
            "reason": "why learn this and in this order",
            "milestones": ["milestone1", "milestone2"]
        }}
    ],
    "total_estimated_weeks": <number>,
    "recommended_approach": "overall strategy in 2-3 sentences"
}}
"""