import os
import json
import streamlit as st
from openai import OpenAI

# -------------------------------------------------
# PAGE SETTINGS
# -------------------------------------------------

st.set_page_config(
    page_title="AI Interview Helper",
    page_icon="🎯",
    layout="wide"
)

# -------------------------------------------------
# CUSTOM STYLE
# -------------------------------------------------

st.markdown("""
<style>

.block-container {
    padding-top: 2rem;
    max-width: 1100px;
}

h1 {
    font-size: 2.5rem;
}

.score-card {
    padding: 18px;
    border: 1px solid #ddd;
    border-radius: 14px;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------

if "question" not in st.session_state:
    st.session_state.question = ""

if "evaluation" not in st.session_state:
    st.session_state.evaluation = None

if "history" not in st.session_state:
    st.session_state.history = []

# -------------------------------------------------
# OPENAI API
# -------------------------------------------------

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.warning(
        "OPENAI_API_KEY is not configured. "
        "Please set your OpenAI API key in the terminal."
    )
    st.stop()

client = OpenAI(api_key=api_key)

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6")

# -------------------------------------------------
# AI HELPER FUNCTION
# -------------------------------------------------

def ask_ai(instructions, user_input):

    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=user_input
    )

    return response.output_text


# -------------------------------------------------
# GENERATE INTERVIEW QUESTION
# -------------------------------------------------

def generate_question(
    role,
    technologies,
    level,
    interview_type
):

    instructions = """
You are a professional IT/software interviewer.

Generate exactly ONE realistic interview question.

Rules:

- Match the candidate's job role.
- Match their technologies.
- Match their experience level.
- Match the interview type.
- Ask only one question.
- Do not provide the answer.
- Make the question realistic.
- Avoid unnecessary explanation.

For coding interviews:
Provide a short problem statement.

For behavioral interviews:
Ask a realistic workplace scenario.

For technical interviews:
Test practical understanding instead of only definitions.

Return only the interview question.
"""

    user_input = f"""
Target Role:
{role}

Technologies:
{technologies}

Experience Level:
{level}

Interview Type:
{interview_type}
"""

    return ask_ai(
        instructions,
        user_input
    )


# -------------------------------------------------
# EVALUATE CANDIDATE ANSWER
# -------------------------------------------------

def evaluate_answer(
    question,
    answer,
    role,
    technologies,
    level
):

    instructions = """
You are an expert IT/software interviewer
and interview coach.

Evaluate the candidate's interview answer.

Return ONLY valid JSON using exactly this format:

{
  "score": 0,
  "technical_accuracy": 0,
  "clarity": 0,
  "completeness": 0,
  "strengths": ["..."],
  "improvements": ["..."],
  "missing_points": ["..."],
  "better_answer": "...",
  "short_answer": "...",
  "follow_up_question": "..."
}

SCORING RULES:

score:
Overall interview score from 0 to 10.

technical_accuracy:
Technical correctness from 0 to 10.

clarity:
How clearly the candidate explained the answer.

completeness:
How completely the candidate answered the question.


IMPORTANT RULES FOR better_answer:

The better_answer must sound like
a REAL HUMAN speaking naturally
during a professional interview.

Humanize the answer.

Use:
- simple professional English
- conversational wording
- natural sentence structure
- practical explanations
- short examples when useful

Avoid:
- robotic wording
- textbook-style definitions
- unnecessary technical jargon
- very long sentences
- overly formal language
- AI-sounding phrases

Use natural phrases when appropriate such as:

"For example..."

"In practice..."

"The main difference is..."

"The way I usually look at it is..."

"If I were implementing this..."

"One common scenario would be..."

"In a real project..."

Keep the better answer approximately
100 to 180 words.

The candidate should be able to
comfortably speak the answer aloud.

Match the candidate's experience level.

IMPORTANT:

If the candidate is a fresher,
do NOT invent professional work experience.

If the candidate has experience,
you may explain practical usage,
but DO NOT invent companies,
projects, achievements,
clients, or work history.

Maintain technical accuracy.


RULES FOR short_answer:

Create a short spoken answer
that can normally be delivered
in about 30 to 60 seconds.

Use approximately 60 to 100 words.

The short answer should:

- sound natural
- be easy to remember
- contain the important technical points
- avoid unnecessary details
- sound like something a candidate
  would genuinely say during an interview


FOLLOW-UP QUESTION:

Generate one realistic interviewer
follow-up question based on the topic.

Be constructive.

Never reward an incorrect answer
simply because it sounds confident.
"""

    user_input = f"""
Target Role:
{role}

Technologies:
{technologies}

Experience Level:
{level}

Interview Question:
{question}

Candidate Answer:
{answer}
"""

    raw = ask_ai(
        instructions,
        user_input
    )

    cleaned = raw.strip()

    # Remove markdown JSON formatting if returned
    if cleaned.startswith("```"):
        cleaned = cleaned.replace(
            "```json",
            "",
            1
        )

        cleaned = cleaned.replace(
            "```",
            ""
        ).strip()

    try:

        return json.loads(cleaned)

    except json.JSONDecodeError:

        return {

            "score": 0,

            "technical_accuracy": 0,

            "clarity": 0,

            "completeness": 0,

            "strengths": [],

            "improvements": [
                "The AI response could not be parsed."
            ],

            "missing_points": [],

            "better_answer": raw,

            "short_answer": raw,

            "follow_up_question": ""
        }


# -------------------------------------------------
# MAIN PAGE
# -------------------------------------------------

st.title("🎯 AI Interview Helper")

st.caption(
    "Practice IT/software interviews, "
    "answer realistic questions and receive "
    "humanized interview-ready feedback."
)

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------

with st.sidebar:

    st.header("Interview Setup")

    role = st.selectbox(
        "Target Role",
        [
            "Python Developer",
            "Software Developer",
            "Data Analyst",
            "Data Engineer",
            "ServiceNow Developer",
            "Cloud Engineer",
            "DevOps Engineer",
            "QA / Test Engineer",
            "Frontend Developer",
            "Backend Developer",
            "Full Stack Developer",
            "Cybersecurity Analyst"
        ]
    )

    technologies = st.text_input(
        "Technologies / Skills",
        value="Python, SQL, Git"
    )

    level = st.selectbox(
        "Experience Level",
        [
            "Fresher",
            "1-2 years",
            "2-4 years",
            "4-7 years",
            "Senior"
        ]
    )

    interview_type = st.selectbox(
        "Interview Type",
        [
            "Technical",
            "Coding",
            "Scenario-based",
            "Behavioral",
            "System Design",
            "HR"
        ]
    )

    st.divider()

    st.info(
        "Use this application for interview "
        "practice and preparation."
    )


# -------------------------------------------------
# TWO COLUMN LAYOUT
# -------------------------------------------------

left, right = st.columns(
    [1.2, 1]
)

# -------------------------------------------------
# LEFT SIDE
# -------------------------------------------------

with left:

    st.subheader(
        "1. Interview Question"
    )

    generate_button = st.button(
        "Generate Question",
        type="primary",
        use_container_width=True
    )

    if generate_button:

        with st.spinner(
            "Generating interview question..."
        ):

            st.session_state.question = (
                generate_question(
                    role,
                    technologies,
                    level,
                    interview_type
                )
            )

            st.session_state.evaluation = None


    if st.session_state.question:

        st.markdown(
            "### Question"
        )

        st.write(
            st.session_state.question
        )

        answer = st.text_area(
            "Your Answer",
            height=220,
            placeholder=(
                "Type your interview answer here..."
            )
        )

        evaluate_button = st.button(
            "Evaluate My Answer",
            use_container_width=True
        )

        if evaluate_button:

            if not answer.strip():

                st.warning(
                    "Please enter your answer first."
                )

            else:

                with st.spinner(
                    "Evaluating your answer..."
                ):

                    result = evaluate_answer(
                        st.session_state.question,
                        answer,
                        role,
                        technologies,
                        level
                    )

                    st.session_state.evaluation = result

                    st.session_state.history.append(
                        {
                            "question":
                                st.session_state.question,

                            "answer":
                                answer,

                            "evaluation":
                                result
                        }
                    )


# -------------------------------------------------
# RIGHT SIDE
# -------------------------------------------------

with right:

    st.subheader(
        "2. Interview Feedback"
    )

    result = st.session_state.evaluation

    if result:

        col1, col2 = st.columns(2)

        col1.metric(
            "Overall Score",
            f"{result.get('score', 0)}/10"
        )

        col2.metric(
            "Technical Accuracy",
            f"{result.get('technical_accuracy', 0)}/10"
        )

        col3, col4 = st.columns(2)

        col3.metric(
            "Clarity",
            f"{result.get('clarity', 0)}/10"
        )

        col4.metric(
            "Completeness",
            f"{result.get('completeness', 0)}/10"
        )


        st.markdown(
            "#### ✅ Strengths"
        )

        strengths = result.get(
            "strengths",
            []
        )

        if strengths:

            for item in strengths:

                st.write(
                    f"✅ {item}"
                )

        else:

            st.write(
                "No strengths returned."
            )


        st.markdown(
            "#### 🔧 Areas to Improve"
        )

        improvements = result.get(
            "improvements",
            []
        )

        if improvements:

            for item in improvements:

                st.write(
                    f"🔧 {item}"
                )


        st.markdown(
            "#### 📌 Missing Points"
        )

        missing = result.get(
            "missing_points",
            []
        )

        if missing:

            for item in missing:

                st.write(
                    f"• {item}"
                )

        else:

            st.write(
                "No major missing points."
            )


        with st.expander(
            "🧑 Humanized Interview Answer"
        ):

            st.write(
                result.get(
                    "better_answer",
                    ""
                )
            )


        with st.expander(
            "⚡ 30–60 Second Answer"
        ):

            st.write(
                result.get(
                    "short_answer",
                    ""
                )
            )


        follow_up = result.get(
            "follow_up_question",
            ""
        )

        if follow_up:

            st.markdown(
                "#### 🎯 Interviewer Follow-up"
            )

            st.write(
                follow_up
            )

    else:

        st.info(
            "Generate a question and submit "
            "your answer to see feedback."
        )


# -------------------------------------------------
# HISTORY
# -------------------------------------------------

st.divider()

st.subheader(
    "📊 Practice History"
)

if st.session_state.history:

    scores = [

        item["evaluation"].get(
            "score",
            0
        )

        for item
        in st.session_state.history

    ]

    average = (
        sum(scores) /
        len(scores)
    )

    st.metric(
        "Average Score",
        f"{average:.1f}/10"
    )


    for i, item in enumerate(
        reversed(
            st.session_state.history
        ),
        1
    ):

        attempt_number = (
            len(
                st.session_state.history
            )
            - i
            + 1
        )

        score = item[
            "evaluation"
        ].get(
            "score",
            0
        )

        with st.expander(
            f"Attempt {attempt_number} "
            f"— Score {score}/10"
        ):

            st.write(
                "**Question:**"
            )

            st.write(
                item["question"]
            )

            st.write(
                "**Your Answer:**"
            )

            st.write(
                item["answer"]
            )

            st.write(
                "**Humanized Answer:**"
            )

            st.write(
                item[
                    "evaluation"
                ].get(
                    "better_answer",
                    ""
                )
            )

else:

    st.caption(
        "Your completed interview "
        "practice attempts will appear here."
    )