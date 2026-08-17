import os
import json
import streamlit as st

from google import genai
from google.genai import types


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Madpirate AI Interview Helper",
    page_icon="🏴‍☠️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# CUSTOM MODERN UI
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 1200px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    [data-testid="stSidebar"] {
        display: none;
    }

    .hero {
        padding: 24px 28px;
        border-radius: 22px;
        border: 1px solid rgba(128,128,128,.22);
        margin-bottom: 20px;
    }

    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .hero-sub {
        opacity: .72;
        font-size: 1rem;
    }

    div[data-testid="stButton"] > button {
        border-radius: 14px;
        min-height: 44px;
    }

    div[data-testid="stPopover"] > button {
        border-radius: 14px;
        min-height: 44px;
    }

    div[data-testid="stTextArea"] textarea {
        border-radius: 16px;
    }

    div[data-testid="stAudioInput"] {
        border-radius: 18px;
    }

    .section-card {
        padding: 20px;
        border-radius: 18px;
        border: 1px solid rgba(128,128,128,.20);
        margin-bottom: 16px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "page": "home",
    "question": "",
    "voice_question": "",
    "voice_answer": "",
    "result": None,
    "history": [],
    "last_audio_answer_id": "",
    "last_audio_question_id": "",
    "role": "Python Developer",
    "technologies": "Python, SQL, Git",
    "experience": "1-2 years",
    "interview_type": "Technical"
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# GEMINI SETTINGS
# ============================================================

def get_api_key():

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        try:
            api_key = st.secrets.get(
                "GEMINI_API_KEY",
                None
            )
        except Exception:
            api_key = None

    return api_key


def get_model():

    model = os.getenv("GEMINI_MODEL")

    if not model:
        try:
            model = st.secrets.get(
                "GEMINI_MODEL",
                "gemini-3.5-flash-lite"
            )
        except Exception:
            model = "gemini-3.5-flash-lite"

    return model


def get_client():

    api_key = get_api_key()

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    return genai.Client(
        api_key=api_key
    )


# ============================================================
# GEMINI TEXT
# ============================================================

def ask_gemini(prompt):

    client = get_client()

    response = client.models.generate_content(
        model=get_model(),
        contents=prompt
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return response.text.strip()


# ============================================================
# AUDIO
# ============================================================

def transcribe_audio(audio_file):

    client = get_client()

    audio_bytes = audio_file.getvalue()

    if not audio_bytes:
        raise RuntimeError(
            "No audio was received."
        )

    audio_part = types.Part.from_bytes(
        data=audio_bytes,
        mime_type="audio/wav"
    )

    response = client.models.generate_content(
        model=get_model(),
        contents=[
            audio_part,
            (
                "Transcribe this spoken English audio accurately. "
                "Return only the spoken words. "
                "Do not explain or summarize."
            )
        ]
    )

    if not response.text:
        raise RuntimeError(
            "No transcription was returned."
        )

    return response.text.strip()


# ============================================================
# QUESTION GENERATION
# ============================================================

def generate_interview_question():

    prompt = f"""
You are a professional IT/software interviewer.

Generate exactly ONE realistic interview question.

Role:
{st.session_state.role}

Technologies:
{st.session_state.technologies}

Experience:
{st.session_state.experience}

Interview Type:
{st.session_state.interview_type}

The question may be technical or non-technical.

Rules:

- Ask only one question.
- Match the experience level.
- Keep it concise.
- Do not provide the answer.
- Return only the question.
"""

    return ask_gemini(prompt)


# ============================================================
# ANSWER GENERATION
# ============================================================

def generate_answer(question):

    prompt = f"""
You are an expert IT/software interview preparation assistant.

Candidate:

Role:
{st.session_state.role}

Technologies:
{st.session_state.technologies}

Experience:
{st.session_state.experience}

Question:
{question}

Return ONLY valid JSON:

{{
    "category": "",
    "humanized_answer": "",
    "short_answer": "",
    "key_points": [
        "",
        "",
        ""
    ],
    "example": "",
    "follow_up_question": ""
}}

Rules:

HUMANIZED ANSWER:
- Be accurate.
- Sound natural and conversational.
- Use simple professional English.
- Avoid robotic or textbook wording.
- Approximately 80 to 130 words.
- Add a practical example when useful.
- Never invent work experience, employers, projects or achievements.

SHORT ANSWER:
- 40 to 70 words.
- Easy to speak in an interview.

KEY POINTS:
- Maximum three.

If the question depends on changing/current information
and certainty is low, say current verification is recommended.
"""

    raw = ask_gemini(prompt)

    cleaned = (
        raw.replace("```json", "")
        .replace("```", "")
        .strip()
    )

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:
        return {
            "category": "General",
            "humanized_answer": raw,
            "short_answer": raw,
            "key_points": [],
            "example": "",
            "follow_up_question": ""
        }


# ============================================================
# EVALUATION
# ============================================================

def evaluate_answer(question, candidate_answer):

    prompt = f"""
You are an expert interview coach.

Candidate Role:
{st.session_state.role}

Technologies:
{st.session_state.technologies}

Experience:
{st.session_state.experience}

Question:
{question}

Candidate Answer:
{candidate_answer}

Return ONLY valid JSON:

{{
    "score": 0,
    "technical_accuracy": 0,
    "clarity": 0,
    "completeness": 0,
    "strengths": [],
    "improvements": [],
    "humanized_answer": "",
    "short_answer": "",
    "follow_up_question": ""
}}

Rules:

- Scores are 0 to 10.
- Correct technical errors.
- Do not reward incorrect content.
- Humanized answer should be natural and concise.
- Do not invent candidate experience.
"""

    raw = ask_gemini(prompt)

    cleaned = (
        raw.replace("```json", "")
        .replace("```", "")
        .strip()
    )

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:
        return {
            "score": 0,
            "technical_accuracy": 0,
            "clarity": 0,
            "completeness": 0,
            "strengths": [],
            "improvements": [],
            "humanized_answer": raw,
            "short_answer": raw,
            "follow_up_question": ""
        }


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">
            🏴‍☠️ Madpirate AI
        </div>

        <div class="hero-sub">
            Smart Interview Helper for technical,
            behavioral and HR interview preparation.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# ICON NAVIGATION
# ============================================================

nav1, nav2, nav3, nav4, nav5, spacer = st.columns(
    [1, 1, 1, 1, 1, 6]
)


with nav1:

    if st.button(
        "",
        icon=":material/home:",
        help="Home",
        use_container_width=True
    ):

        st.session_state.page = "home"
        st.rerun()


with nav2:

    if st.button(
        "",
        icon=":material/mic:",
        help="Mock Interview",
        use_container_width=True
    ):

        st.session_state.page = "interview"
        st.rerun()


with nav3:

    if st.button(
        "",
        icon=":material/chat:",
        help="Ask Any Question",
        use_container_width=True
    ):

        st.session_state.page = "ask"
        st.rerun()


with nav4:

    if st.button(
        "",
        icon=":material/history:",
        help="History",
        use_container_width=True
    ):

        st.session_state.page = "history"
        st.rerun()


# ============================================================
# SETTINGS POPOVER
# ============================================================

with nav5:

    with st.popover(
        "",
        icon=":material/settings:",
        help="Interview Settings",
        use_container_width=True
    ):

        st.subheader(
            "Interview Settings"
        )

        st.session_state.role = st.selectbox(
            "Target Role",
            [
                "Python Developer",
                "Software Developer",
                "Data Analyst",
                "Data Engineer",
                "ServiceNow Developer",
                "DevOps Engineer",
                "Cloud Engineer",
                "QA / Test Engineer",
                "Frontend Developer",
                "Backend Developer",
                "Full Stack Developer",
                "Cybersecurity Analyst",
                "General IT"
            ],
            index=[
                "Python Developer",
                "Software Developer",
                "Data Analyst",
                "Data Engineer",
                "ServiceNow Developer",
                "DevOps Engineer",
                "Cloud Engineer",
                "QA / Test Engineer",
                "Frontend Developer",
                "Backend Developer",
                "Full Stack Developer",
                "Cybersecurity Analyst",
                "General IT"
            ].index(st.session_state.role)
        )

        st.session_state.technologies = st.text_input(
            "Technologies / Skills",
            value=st.session_state.technologies
        )

        st.session_state.experience = st.selectbox(
            "Experience Level",
            [
                "Fresher",
                "1-2 years",
                "2-4 years",
                "4-7 years",
                "Senior"
            ],
            index=[
                "Fresher",
                "1-2 years",
                "2-4 years",
                "4-7 years",
                "Senior"
            ].index(
                st.session_state.experience
            )
        )

        st.session_state.interview_type = st.selectbox(
            "Interview Type",
            [
                "Mixed",
                "Technical",
                "Coding",
                "Scenario-based",
                "Behavioral",
                "System Design",
                "HR"
            ],
            index=[
                "Mixed",
                "Technical",
                "Coding",
                "Scenario-based",
                "Behavioral",
                "System Design",
                "HR"
            ].index(
                st.session_state.interview_type
            )
        )

        st.caption(
            f"Model: {get_model()}"
        )

        if get_api_key():
            st.success(
                "Gemini connected"
            )
        else:
            st.error(
                "Gemini API key missing"
            )


st.divider()


# ============================================================
# HOME
# ============================================================

if st.session_state.page == "home":

    st.subheader(
        "Welcome to Madpirate AI"
    )

    st.write(
        "Choose an icon above to start."
    )

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            """
            <div class="section-card">
            <h3>🎤 Mock Interview</h3>
            Practice realistic technical, behavioral and HR
            interview questions with voice support.
            </div>
            """,
            unsafe_allow_html=True
        )


    with c2:

        st.markdown(
            """
            <div class="section-card">
            <h3>💬 Ask Any Question</h3>
            Ask technical or non-technical interview
            questions and receive humanized answers.
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# MOCK INTERVIEW
# ============================================================

elif st.session_state.page == "interview":

    left, right = st.columns(
        [1.05, 1]
    )


    with left:

        st.subheader(
            "🎤 Mock Interview"
        )


        if st.button(
            "Generate Question",
            icon=":material/auto_awesome:",
            type="primary",
            use_container_width=True
        ):

            try:

                with st.spinner(
                    "Preparing question..."
                ):

                    st.session_state.question = (
                        generate_interview_question()
                    )

                st.session_state.result = None
                st.session_state.voice_answer = ""

            except Exception as error:

                st.error(
                    str(error)
                )


        if st.session_state.question:

            st.info(
                st.session_state.question
            )


            audio = st.audio_input(
                "Speak your answer",
                sample_rate=16000
            )


            if audio is not None:

                audio_id = str(
                    hash(
                        audio.getvalue()
                    )
                )


                if (
                    audio_id
                    !=
                    st.session_state.last_audio_answer_id
                ):

                    st.session_state.last_audio_answer_id = (
                        audio_id
                    )


                    try:

                        with st.spinner(
                            "Listening..."
                        ):

                            st.session_state.voice_answer = (
                                transcribe_audio(
                                    audio
                                )
                            )

                    except Exception as error:

                        st.error(
                            f"Audio error: {error}"
                        )


            candidate_answer = st.text_area(
                "Your Answer",
                value=st.session_state.voice_answer,
                height=180
            )


            if st.button(
                "Evaluate Answer",
                icon=":material/bolt:",
                type="primary",
                use_container_width=True
            ):

                if candidate_answer.strip():

                    try:

                        with st.spinner(
                            "Analyzing..."
                        ):

                            result = evaluate_answer(
                                st.session_state.question,
                                candidate_answer
                            )

                            st.session_state.result = (
                                result
                            )

                            st.session_state.history.append(
                                {
                                    "question":
                                        st.session_state.question,

                                    "answer":
                                        candidate_answer,

                                    "result":
                                        result
                                }
                            )

                    except Exception as error:

                        st.error(
                            str(error)
                        )


    with right:

        st.subheader(
            "AI Feedback"
        )


        result = st.session_state.result


        if result:

            a, b = st.columns(2)

            a.metric(
                "Overall",
                f"{result.get('score', 0)}/10"
            )

            b.metric(
                "Technical",
                f"{result.get('technical_accuracy', 0)}/10"
            )


            st.markdown(
                "### Humanized Answer"
            )

            st.write(
                result.get(
                    "humanized_answer",
                    ""
                )
            )


            with st.expander(
                "Quick Answer",
                icon=":material/bolt:",
                expanded=True
            ):

                st.write(
                    result.get(
                        "short_answer",
                        ""
                    )
                )


            st.markdown(
                "### Follow-up"
            )

            st.write(
                result.get(
                    "follow_up_question",
                    ""
                )
            )


        else:

            st.info(
                "Your feedback appears here."
            )


# ============================================================
# ASK ANY QUESTION
# ============================================================

elif st.session_state.page == "ask":

    st.subheader(
        "💬 Ask Madpirate AI"
    )


    audio_question = st.audio_input(
        "Ask by voice",
        sample_rate=16000
    )


    if audio_question is not None:

        audio_id = str(
            hash(
                audio_question.getvalue()
            )
        )


        if (
            audio_id
            !=
            st.session_state.last_audio_question_id
        ):

            st.session_state.last_audio_question_id = (
                audio_id
            )


            try:

                with st.spinner(
                    "Listening..."
                ):

                    st.session_state.voice_question = (
                        transcribe_audio(
                            audio_question
                        )
                    )

            except Exception as error:

                st.error(
                    f"Audio error: {error}"
                )


    question = st.text_area(
        "Your Question",
        value=st.session_state.voice_question,
        height=130,
        placeholder=(
            "Ask Python, SQL, ServiceNow, DevOps, HR, "
            "behavioral or other interview questions..."
        )
    )


    if st.button(
        "Get Answer",
        icon=":material/bolt:",
        type="primary",
        use_container_width=True
    ):

        if question.strip():

            try:

                with st.spinner(
                    "Generating answer..."
                ):

                    st.session_state.result = (
                        generate_answer(
                            question
                        )
                    )

            except Exception as error:

                st.error(
                    str(error)
                )


    result = st.session_state.result


    if result:

        st.markdown(
            "### Humanized Answer"
        )

        st.write(
            result.get(
                "humanized_answer",
                ""
            )
        )


        with st.expander(
            "Quick Answer",
            icon=":material/bolt:",
            expanded=True
        ):

            st.write(
                result.get(
                    "short_answer",
                    ""
                )
            )


        with st.expander(
            "Key Points",
            icon=":material/checklist:"
        ):

            for point in result.get(
                "key_points",
                []
            ):

                st.write(
                    f"• {point}"
                )


        example = result.get(
            "example",
            ""
        )


        if example:

            with st.expander(
                "Example",
                icon=":material/lightbulb:"
            ):

                st.write(
                    example
                )


# ============================================================
# HISTORY
# ============================================================

elif st.session_state.page == "history":

    st.subheader(
        "📚 Practice History"
    )


    if not st.session_state.history:

        st.info(
            "No interview history yet."
        )


    else:

        for number, item in enumerate(
            reversed(
                st.session_state.history
            ),
            start=1
        ):

            with st.expander(
                f"Attempt {number}",
                icon=":material/history:"
            ):

                st.write(
                    "**Question**"
                )

                st.write(
                    item["question"]
                )


                st.write(
                    "**Your Answer**"
                )

                st.write(
                    item["answer"]
                )


                st.write(
                    "**Improved Answer**"
                )

                st.write(
                    item[
                        "result"
                    ].get(
                        "humanized_answer",
                        ""
                    )
                )