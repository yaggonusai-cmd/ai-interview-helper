import os
import json
import random
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="AI Interview Helper",
    page_icon="🎯",
    layout="wide"
)

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
# TEST QUESTIONS
# -------------------------------------------------

TEST_QUESTIONS = {
    "Python Developer": [
        "What is the difference between a Python list and a tuple?",
        "Explain the difference between == and is in Python.",
        "What is a Python decorator and when would you use one?",
        "Explain exception handling in Python.",
        "What is the difference between shallow copy and deep copy?"
    ],

    "Software Developer": [
        "What is object-oriented programming?",
        "Explain the difference between a process and a thread.",
        "What is an API and how is it used?",
        "What is version control and why is Git useful?",
        "Explain the difference between frontend and backend development."
    ],

    "Data Analyst": [
        "What is the difference between INNER JOIN and LEFT JOIN in SQL?",
        "How would you handle missing values in a dataset?",
        "What is data normalization?",
        "Explain the difference between WHERE and HAVING in SQL.",
        "How would you identify duplicate records in SQL?"
    ],

    "ServiceNow Developer": [
        "What is the difference between a Client Script and a Business Rule?",
        "What is a Script Include in ServiceNow?",
        "What is GlideRecord?",
        "What is the difference between UI Policy and Data Policy?",
        "Explain how ACLs work in ServiceNow."
    ],

    "DevOps Engineer": [
        "What is CI/CD?",
        "What is Docker and why is it used?",
        "What is the difference between Git merge and Git rebase?",
        "What is Infrastructure as Code?",
        "What is Kubernetes used for?"
    ],

    "Cloud Engineer": [
        "What is cloud computing?",
        "What is the difference between IaaS, PaaS, and SaaS?",
        "What is auto scaling?",
        "What is a load balancer?",
        "What is the difference between public and private cloud?"
    ]
}

DEFAULT_QUESTIONS = [
    "Tell me about yourself from a technical perspective.",
    "Describe a technical problem you solved.",
    "How do you approach debugging an application?",
    "What steps do you follow when learning a new technology?",
    "How do you make sure your code is reliable?"
]

# -------------------------------------------------
# TEST MODE HUMANIZED ANSWERS
# -------------------------------------------------

TEST_ANSWERS = {

    "What is the difference between a Python list and a tuple?": {
        "better_answer":
            "The main difference is that a list is mutable, which means I can "
            "add, remove, or change items after creating it. A tuple is immutable, "
            "so once it is created, its values cannot be changed. In practice, I "
            "would use a list when the data may change during the program, such as "
            "items in a shopping cart. I would use a tuple for values that should "
            "stay fixed, such as coordinates. Lists use square brackets, while "
            "tuples normally use parentheses.",

        "short_answer":
            "The main difference is mutability. Lists can be modified after "
            "creation, while tuples cannot. I normally use a list for data that "
            "changes and a tuple for fixed values. For example, shopping cart "
            "items could be stored in a list, while coordinates could be stored "
            "in a tuple."
    },

    "What is the difference between a Client Script and a Business Rule?": {
        "better_answer":
            "The main difference is where they execute. A Client Script runs in "
            "the user's browser and is mainly used to control form behavior, such "
            "as making a field mandatory or showing a message. A Business Rule "
            "runs on the server and is used when records are inserted, updated, "
            "deleted, or queried. For example, if I want to automatically update "
            "a field before saving a record, I would normally use a Business Rule. "
            "If I want to change how the form behaves while the user is filling it "
            "out, I would use a Client Script.",

        "short_answer":
            "A Client Script runs on the client side and controls form behavior. "
            "A Business Rule runs on the server side and handles record processing. "
            "For example, I would use a Client Script to make a field mandatory "
            "and a Business Rule to update a value when a record is saved."
    },

    "What is the difference between INNER JOIN and LEFT JOIN in SQL?": {
        "better_answer":
            "An INNER JOIN returns only the rows that have matching values in both "
            "tables. A LEFT JOIN returns all rows from the left table and the "
            "matching rows from the right table. If there is no match, the right "
            "side contains NULL values. In practice, I use INNER JOIN when I only "
            "need records that exist in both tables. I use LEFT JOIN when I still "
            "want to keep every record from the main table, even if related data "
            "is missing.",

        "short_answer":
            "INNER JOIN returns only matching rows from both tables. LEFT JOIN "
            "returns every row from the left table and matching rows from the "
            "right table. If there is no match, the right-side values are NULL."
    }
}

# -------------------------------------------------
# OPENAI SETUP
# -------------------------------------------------

def get_api_key():
    # Works locally with environment variable
    key = os.getenv("OPENAI_API_KEY")

    # Works on Streamlit Cloud with secrets
    if not key:
        try:
            key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            key = None

    return key


def get_model():
    model = os.getenv("OPENAI_MODEL")

    if not model:
        try:
            model = st.secrets.get("OPENAI_MODEL", "gpt-5.6")
        except Exception:
            model = "gpt-5.6"

    return model


# -------------------------------------------------
# REAL AI FUNCTIONS
# -------------------------------------------------

def ask_ai(instructions, user_input):

    api_key = get_api_key()

    if not api_key:
        raise Exception("OPENAI_API_KEY is not configured.")

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=get_model(),
        instructions=instructions,
        input=user_input
    )

    return response.output_text


def generate_real_question(role, technologies, level, interview_type):

    instructions = """
You are a professional IT/software interviewer.

Generate exactly ONE realistic interview question.

Match:
- target role
- technologies
- experience level
- interview type

Do not provide the answer.
Return only the interview question.
"""

    user_input = f"""
Role: {role}
Technologies: {technologies}
Experience: {level}
Interview Type: {interview_type}
"""

    return ask_ai(instructions, user_input)


def evaluate_real_answer(question, answer, role, technologies, level):

    instructions = """
You are an expert IT interview coach.

Return ONLY valid JSON:

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

The better_answer must sound natural and human.

Rules:
- Use simple professional English.
- Avoid robotic or textbook language.
- Keep answers conversational.
- Use practical examples.
- Do not invent experience.
- Keep the better answer around 100 to 180 words.
- Keep short_answer around 60 to 100 words.
"""

    user_input = f"""
Role: {role}
Technologies: {technologies}
Experience: {level}

Question:
{question}

Candidate Answer:
{answer}
"""

    raw = ask_ai(instructions, user_input)

    cleaned = raw.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "", 1)
        cleaned = cleaned.replace("```", "").strip()

    return json.loads(cleaned)


# -------------------------------------------------
# TEST MODE FUNCTIONS
# -------------------------------------------------

def generate_test_question(role):

    questions = TEST_QUESTIONS.get(
        role,
        DEFAULT_QUESTIONS
    )

    return random.choice(questions)


def evaluate_test_answer(question, answer):

    answer_length = len(answer.split())

    if answer_length < 10:
        score = 4
    elif answer_length < 25:
        score = 6
    elif answer_length < 60:
        score = 8
    else:
        score = 9

    sample = TEST_ANSWERS.get(question)

    if sample:
        better_answer = sample["better_answer"]
        short_answer = sample["short_answer"]

    else:
        better_answer = (
            "A good way to answer this is to first explain the concept clearly, "
            "then give one practical example. I would keep the explanation simple "
            "and focus on how the technology is actually used. In a real interview, "
            "I would avoid giving only a definition and instead explain when I "
            "would use the concept and why."
        )

        short_answer = (
            "I would explain the main concept first and then give a practical "
            "example. That helps show both technical understanding and how the "
            "concept is used in a real situation."
        )

    return {
        "score": score,
        "technical_accuracy": score,
        "clarity": max(score - 1, 1),
        "completeness": score,
        "strengths": [
            "You attempted to explain the concept.",
            "Your answer can be improved with practical examples."
        ],
        "improvements": [
            "Structure your answer more clearly.",
            "Add one real-world example.",
            "Focus on the most important technical points."
        ],
        "missing_points": [
            "A practical use case may improve the answer."
        ],
        "better_answer": better_answer,
        "short_answer": short_answer,
        "follow_up_question":
            "Can you give me a practical example of when you would use this?"
    }


# -------------------------------------------------
# UI
# -------------------------------------------------

st.title("🎯 AI Interview Helper")

st.caption(
    "Practice IT/software interviews and improve your answers."
)

with st.sidebar:

    st.header("Interview Setup")

    mode = st.radio(
        "Application Mode",
        [
            "🧪 Test Mode - Free",
            "🤖 Real AI Mode"
        ]
    )

    role = st.selectbox(
        "Target Role",
        [
            "Python Developer",
            "Software Developer",
            "Data Analyst",
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

    if mode.startswith("🧪"):
        st.success(
            "Test Mode is active. No API credits are used."
        )
    else:
        st.warning(
            "Real AI Mode uses your OpenAI API credits."
        )

# -------------------------------------------------
# QUESTION
# -------------------------------------------------

left, right = st.columns([1.2, 1])

with left:

    st.subheader("1. Interview Question")

    if st.button(
        "Generate Question",
        type="primary",
        use_container_width=True
    ):

        st.session_state.evaluation = None

        if mode.startswith("🧪"):

            st.session_state.question = (
                generate_test_question(role)
            )

        else:

            try:

                with st.spinner(
                    "Generating AI interview question..."
                ):

                    st.session_state.question = (
                        generate_real_question(
                            role,
                            technologies,
                            level,
                            interview_type
                        )
                    )

            except Exception as e:

                st.error(
                    f"AI request failed: {e}"
                )

    if st.session_state.question:

        st.markdown("### Question")

        st.write(
            st.session_state.question
        )

        answer = st.text_area(
            "Your Answer",
            height=220,
            placeholder="Type your interview answer here..."
        )

        if st.button(
            "Evaluate My Answer",
            use_container_width=True
        ):

            if not answer.strip():

                st.warning(
                    "Please enter your answer first."
                )

            else:

                if mode.startswith("🧪"):

                    result = evaluate_test_answer(
                        st.session_state.question,
                        answer
                    )

                else:

                    try:

                        with st.spinner(
                            "Evaluating your answer..."
                        ):

                            result = evaluate_real_answer(
                                st.session_state.question,
                                answer,
                                role,
                                technologies,
                                level
                            )

                    except Exception as e:

                        st.error(
                            f"AI evaluation failed: {e}"
                        )

                        result = None

                if result:

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
# FEEDBACK
# -------------------------------------------------

with right:

    st.subheader("2. Interview Feedback")

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

        st.markdown("#### ✅ Strengths")

        for item in result.get(
            "strengths",
            []
        ):
            st.write(
                f"✅ {item}"
            )

        st.markdown("#### 🔧 Improvements")

        for item in result.get(
            "improvements",
            []
        ):
            st.write(
                f"🔧 {item}"
            )

        st.markdown("#### 📌 Missing Points")

        for item in result.get(
            "missing_points",
            []
        ):
            st.write(
                f"• {item}"
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

        st.markdown(
            "#### 🎯 Follow-up Question"
        )

        st.write(
            result.get(
                "follow_up_question",
                ""
            )
        )

    else:

        st.info(
            "Generate a question and evaluate "
            "your answer to see feedback."
        )

# -------------------------------------------------
# HISTORY
# -------------------------------------------------

st.divider()

st.subheader("📊 Practice History")

if st.session_state.history:

    scores = [
        item["evaluation"].get("score", 0)
        for item in st.session_state.history
    ]

    average = (
        sum(scores) / len(scores)
    )

    st.metric(
        "Average Score",
        f"{average:.1f}/10"
    )

    for index, item in enumerate(
        reversed(st.session_state.history),
        1
    ):

        with st.expander(
            f"Practice Attempt {index}"
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
                "**Suggested Answer:**"
            )

            st.write(
                item["evaluation"].get(
                    "better_answer",
                    ""
                )
            )

else:

    st.caption(
        "Your completed practice attempts "
        "will appear here."
    )