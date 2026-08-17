import os
import io
import json
import time
import wave
import queue
import random
import threading

import av
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

from openai import OpenAI
from streamlit_webrtc import WebRtcMode, webrtc_streamer


# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="Madpirate AI Interview Helper",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 AI Interview Helper")

st.caption(
    "Hands-free AI mock interview practice for technical "
    "and non-technical interview questions."
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "running": False,
    "question": "",
    "question_number": 0,
    "last_spoken_question": "",
    "transcript": "",
    "evaluation": None,
    "history": [],
    "status": "Ready",
    "next_question_time": 0,
    "last_audio_id": ""
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# OPENAI SETTINGS
# ============================================================

def get_api_key():

    key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not key:

        try:

            key = st.secrets.get(
                "OPENAI_API_KEY",
                None
            )

        except Exception:

            key = None

    return key


def get_model():

    model = os.getenv(
        "OPENAI_MODEL"
    )

    if not model:

        try:

            model = st.secrets.get(
                "OPENAI_MODEL",
                "gpt-5.6"
            )

        except Exception:

            model = "gpt-5.6"

    return model


def get_client():

    api_key = get_api_key()

    if not api_key:

        raise RuntimeError(
            "OPENAI_API_KEY is not configured."
        )

    return OpenAI(
        api_key=api_key
    )


# ============================================================
# TEST QUESTIONS
# ============================================================

TEST_QUESTIONS = {

    "Python Developer": [

        "What is the difference between a Python list and a tuple?",

        "What are Python dictionaries?",

        "Explain exception handling in Python.",

        "What is a Python decorator?",

        "What is the difference between == and is in Python?"
    ],

    "Software Developer": [

        "What is object-oriented programming?",

        "What is an API?",

        "How do you debug an application?",

        "What is version control?",

        "Explain polymorphism."
    ],

    "Data Analyst": [

        "What is the difference between INNER JOIN and LEFT JOIN?",

        "How would you handle missing values?",

        "What is data cleaning?",

        "What is the difference between WHERE and HAVING?",

        "How would you find duplicate records in SQL?"
    ],

    "ServiceNow Developer": [

        "What is the difference between a Client Script and a Business Rule?",

        "What is GlideRecord?",

        "What is a Script Include?",

        "What is an ACL in ServiceNow?",

        "What is a UI Policy?"
    ],

    "DevOps Engineer": [

        "What is CI CD?",

        "What is Docker?",

        "What is Kubernetes?",

        "What is Infrastructure as Code?",

        "What is Git?"
    ],

    "HR / Behavioral": [

        "Tell me about yourself.",

        "Why should we hire you?",

        "What are your strengths?",

        "What is one weakness you are improving?",

        "How do you handle conflict with a coworker?"
    ]
}


# ============================================================
# GENERATE QUESTION
# ============================================================

def generate_question(
    role,
    technologies,
    experience,
    interview_type,
    test_mode
):

    if test_mode:

        questions = TEST_QUESTIONS.get(
            role,
            TEST_QUESTIONS[
                "Software Developer"
            ]
        )

        return random.choice(
            questions
        )

    client = get_client()

    instructions = """
You are a professional IT/software mock interviewer.

Generate exactly ONE interview question.

The question may be technical or non-technical.

Match:

- candidate role
- technologies
- experience level
- interview type

Possible areas include:

Python
Java
JavaScript
SQL
ServiceNow
Cloud
DevOps
Networking
Cybersecurity
Testing
Data Analysis
System Design
HR
Behavioral
Leadership
Communication

Rules:

Ask only ONE question.

Do not provide the answer.

Return only the question.
"""

    prompt = f"""
Role:
{role}

Technologies:
{technologies}

Experience:
{experience}

Interview Type:
{interview_type}
"""

    response = client.responses.create(

        model=get_model(),

        instructions=instructions,

        input=prompt
    )

    return response.output_text.strip()


# ============================================================
# TRANSCRIBE VOICE
# ============================================================

def transcribe_audio(
    wav_bytes
):

    client = get_client()

    audio_file = io.BytesIO(
        wav_bytes
    )

    audio_file.name = (
        "interview_answer.wav"
    )

    transcription = (
        client.audio.transcriptions.create(

            model="gpt-4o-mini-transcribe",

            file=audio_file
        )
    )

    return transcription.text.strip()


# ============================================================
# EVALUATE ANSWER
# ============================================================

def evaluate_answer(
    question,
    candidate_answer,
    role,
    technologies,
    experience
):

    client = get_client()

    instructions = """
You are an expert IT/software interview coach.

The candidate is practicing for an interview.

Evaluate the answer.

Return ONLY JSON:

{
    "score": 0,
    "technical_accuracy": 0,
    "clarity": 0,
    "completeness": 0,
    "question_type": "...",
    "humanized_answer": "...",
    "short_answer": "...",
    "key_points": [
        "...",
        "...",
        "..."
    ],
    "follow_up_question": "..."
}

IMPORTANT:

Scores must be from 0 to 10.

Determine whether the question is:

Technical
Non-Technical
HR
Behavioral
Scenario
Coding
System Design
General

The humanized answer must sound like
a REAL person speaking during an interview.

Use:

simple English
natural language
short sentences
professional wording
practical examples

Avoid:

robotic language
AI-style language
textbook definitions
unnecessary jargon

Do not invent:

companies
projects
employment history
achievements

If the candidate is a fresher,
do not invent professional experience.

The humanized answer should normally
take around 60 to 90 seconds.

The short answer should normally
take around 30 to 60 seconds.

If the original answer contains an
incorrect technical statement,
correct it.
"""

    prompt = f"""
Target Role:
{role}

Technologies:
{technologies}

Experience:
{experience}

Interview Question:
{question}

Candidate Answer:
{candidate_answer}
"""

    response = client.responses.create(

        model=get_model(),

        instructions=instructions,

        input=prompt
    )

    result = response.output_text.strip()

    if result.startswith("```"):

        result = (
            result
            .replace(
                "```json",
                "",
                1
            )
            .replace(
                "```",
                ""
            )
            .strip()
        )

    return json.loads(
        result
    )


# ============================================================
# TEXT TO SPEECH
# ============================================================

def speak_question(
    question
):

    question_json = json.dumps(
        question
    )

    components.html(

        f"""
        <script>

        window.speechSynthesis.cancel();

        const message =
            new SpeechSynthesisUtterance(
                {question_json}
            );

        message.rate = 0.95;

        message.pitch = 1;

        window.speechSynthesis.speak(
            message
        );

        </script>
        """,

        height=0
    )


# ============================================================
# AUTOMATIC VOICE DETECTION
# ============================================================

class AutomaticVoiceDetector:

    def __init__(self):

        self.resampler = (
            av.AudioResampler(

                format="s16",

                layout="mono",

                rate=16000
            )
        )

        self.sample_rate = 16000

        self.audio_chunks = []

        self.is_speaking = False

        self.silence_duration = 0

        self.audio_queue = queue.Queue()

        self.lock = threading.Lock()


        # Increase if background noise triggers detection.
        # Reduce if microphone is quiet.

        self.energy_threshold = 500


        # Automatically finish the answer after
        # approximately this much silence.

        self.required_silence = 1.4


        # Ignore extremely short sounds.

        self.minimum_speech = 0.8


    def recv(
        self,
        frame
    ):

        frames = (
            self.resampler.resample(
                frame
            )
        )

        if not isinstance(
            frames,
            list
        ):

            frames = [frames]


        for frame in frames:

            if frame is None:

                continue


            samples = (
                frame
                .to_ndarray()
                .reshape(-1)
                .astype(
                    np.int16
                )
            )


            if len(samples) == 0:

                continue


            energy = float(

                np.sqrt(

                    np.mean(

                        samples.astype(
                            np.float32
                        ) ** 2

                    )

                )

            )


            duration = (

                len(samples)
                /
                self.sample_rate

            )


            # ------------------------------------------------
            # SPEECH DETECTED
            # ------------------------------------------------

            if (
                energy
                >
                self.energy_threshold
            ):

                self.is_speaking = True

                self.silence_duration = 0

                self.audio_chunks.append(
                    samples.copy()
                )


            # ------------------------------------------------
            # SILENCE
            # ------------------------------------------------

            elif self.is_speaking:

                self.audio_chunks.append(
                    samples.copy()
                )

                self.silence_duration += (
                    duration
                )


                # User stopped talking

                if (

                    self.silence_duration
                    >=
                    self.required_silence

                ):

                    self.finish_answer()


        return frame


    # ========================================================
    # CREATE WAV FILE
    # ========================================================

    def finish_answer(
        self
    ):

        if not self.audio_chunks:

            self.reset()

            return


        audio = np.concatenate(
            self.audio_chunks
        )


        total_duration = (

            len(audio)
            /
            self.sample_rate

        )


        if (

            total_duration
            >=
            self.minimum_speech

        ):

            buffer = io.BytesIO()


            with wave.open(
                buffer,
                "wb"
            ) as wav:

                wav.setnchannels(1)

                wav.setsampwidth(2)

                wav.setframerate(
                    self.sample_rate
                )

                wav.writeframes(
                    audio.tobytes()
                )


            self.audio_queue.put(
                buffer.getvalue()
            )


        self.reset()


    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self
    ):

        self.audio_chunks = []

        self.is_speaking = False

        self.silence_duration = 0


    # ========================================================
    # GET COMPLETED ANSWER
    # ========================================================

    def get_answer_audio(
        self
    ):

        try:

            return (
                self.audio_queue
                .get_nowait()
            )

        except queue.Empty:

            return None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "⚙️ Interview Setup"
    )


    test_mode = st.toggle(
        "🧪 Test Questions",
        value=False
    )


    role = st.selectbox(

        "Target Role",

        [
            "Python Developer",
            "Software Developer",
            "Data Analyst",
            "ServiceNow Developer",
            "DevOps Engineer",
            "Cloud Engineer",
            "QA / Test Engineer",
            "Frontend Developer",
            "Backend Developer",
            "Full Stack Developer",
            "Cybersecurity Analyst",
            "HR / Behavioral"
        ]
    )


    technologies = st.text_input(

        "Technologies",

        value=(
            "Python, SQL, Git"
        )
    )


    experience = st.selectbox(

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
            "Mixed",
            "Technical",
            "Coding",
            "Scenario-based",
            "Behavioral",
            "System Design",
            "HR"
        ]
    )


    wait_seconds = st.slider(

        "Seconds before next question",

        minimum_value := 5,

        maximum_value := 20,

        value=10

    )


# ============================================================
# START INTERVIEW
# ============================================================

col1, col2 = st.columns(
    [1, 1]
)


with col1:

    if not st.session_state.running:

        if st.button(

            "▶ Start Mock Interview",

            type="primary",

            use_container_width=True
        ):

            st.session_state.running = True

            st.session_state.question = ""

            st.session_state.transcript = ""

            st.session_state.evaluation = None

            st.session_state.question_number = 0

            st.session_state.status = (
                "Starting interview..."
            )

            st.rerun()


with col2:

    if st.session_state.running:

        if st.button(

            "■ End Interview",

            use_container_width=True
        ):

            st.session_state.running = False

            st.session_state.status = (
                "Interview ended"
            )

            st.rerun()


st.info(
    f"Status: {st.session_state.status}"
)


# ============================================================
# RUNNING INTERVIEW
# ============================================================

if st.session_state.running:


    # --------------------------------------------------------
    # GENERATE QUESTION AUTOMATICALLY
    # --------------------------------------------------------

    if not st.session_state.question:

        try:

            with st.spinner(
                "Preparing question..."
            ):

                question = (
                    generate_question(

                        role,

                        technologies,

                        experience,

                        interview_type,

                        test_mode
                    )
                )


                st.session_state.question = (
                    question
                )

                st.session_state.question_number += 1

                st.session_state.transcript = ""

                st.session_state.evaluation = None

                st.session_state.status = (
                    "Listening..."
                )


        except Exception as error:

            st.error(
                error
            )

            st.stop()


    # --------------------------------------------------------
    # AUTOMATICALLY READ QUESTION ALOUD
    # --------------------------------------------------------

    if (

        st.session_state.question
        !=
        st.session_state.last_spoken_question

    ):

        speak_question(
            st.session_state.question
        )

        st.session_state.last_spoken_question = (
            st.session_state.question
        )


    left, right = st.columns(
        [1.1, 1]
    )


    # ========================================================
    # LEFT
    # ========================================================

    with left:

        st.subheader(
            f"🎤 Question {st.session_state.question_number}"
        )


        st.info(
            st.session_state.question
        )


        st.markdown(
            "### 🎙️ Automatic Microphone"
        )


        st.caption(
            "Speak naturally. The app detects when you start "
            "and stops processing after you become silent."
        )


        webrtc_context = webrtc_streamer(

            key="automatic-interview-microphone",

            mode=WebRtcMode.SENDONLY,


            # Automatically keep microphone running

            desired_playing_state=True,


            media_stream_constraints={

                "video": False,

                "audio": True

            },


            # Hide microphone media toggle buttons

            media_toggle_controls=False,


            audio_processor_factory=(
                AutomaticVoiceDetector
            ),


            async_processing=True
        )


        if st.session_state.transcript:

            st.markdown(
                "### 📝 Detected Answer"
            )

            st.write(
                st.session_state.transcript
            )


    # ========================================================
    # RIGHT
    # ========================================================

    with right:

        st.subheader(
            "🧠 AI Interview Answer"
        )


        result = (
            st.session_state.evaluation
        )


        if result:


            a, b = st.columns(2)


            a.metric(

                "Overall Score",

                f"{result.get('score', 0)}/10"
            )


            b.metric(

                "Technical Accuracy",

                f"{result.get('technical_accuracy', 0)}/10"
            )


            c, d = st.columns(2)


            c.metric(

                "Clarity",

                f"{result.get('clarity', 0)}/10"
            )


            d.metric(

                "Completeness",

                f"{result.get('completeness', 0)}/10"
            )


            st.caption(

                "Question Type: "

                + result.get(
                    "question_type",
                    "General"
                )

            )


            # ------------------------------------------------
            # HUMANIZED ANSWER
            # ------------------------------------------------

            st.markdown(
                "### 🧑 Humanized Answer"
            )


            st.write(

                result.get(
                    "humanized_answer",
                    ""
                )

            )


            # ------------------------------------------------
            # SHORT ANSWER
            # ------------------------------------------------

            with st.expander(
                "⚡ 30–60 Second Answer",
                expanded=True
            ):

                st.write(

                    result.get(
                        "short_answer",
                        ""
                    )

                )


            # ------------------------------------------------
            # KEY POINTS
            # ------------------------------------------------

            st.markdown(
                "### 📌 Key Points"
            )


            for point in result.get(
                "key_points",
                []
            ):

                st.write(
                    f"• {point}"
                )


            # ------------------------------------------------
            # FOLLOW UP
            # ------------------------------------------------

            st.markdown(
                "### 🎯 Possible Follow-up"
            )


            st.write(

                result.get(
                    "follow_up_question",
                    ""
                )

            )


        else:

            st.info(
                "Answer the question using your voice. "
                "The AI response will appear automatically."
            )


# ============================================================
# AUTOMATIC BACKGROUND CHECK
# ============================================================

@st.fragment(
    run_every=0.75
)

def automatic_processing():


    if not st.session_state.running:

        return


    # --------------------------------------------------------
    # GET MICROPHONE PROCESSOR
    # --------------------------------------------------------

    try:

        processor = (
            webrtc_context
            .audio_processor
        )

    except Exception:

        processor = None


    # --------------------------------------------------------
    # NEW VOICE ANSWER AVAILABLE
    # --------------------------------------------------------

    if (

        processor is not None

        and

        st.session_state.evaluation
        is None

    ):


        audio = (
            processor
            .get_answer_audio()
        )


        if audio:


            audio_id = str(
                hash(audio)
            )


            if (

                audio_id
                !=
                st.session_state.last_audio_id

            ):


                st.session_state.last_audio_id = (
                    audio_id
                )


                st.session_state.status = (
                    "Voice detected — converting to text..."
                )


                try:


                    # ========================================
                    # SPEECH TO TEXT
                    # ========================================

                    transcript = (
                        transcribe_audio(
                            audio
                        )
                    )


                    if transcript:


                        st.session_state.transcript = (
                            transcript
                        )


                        st.session_state.status = (
                            "Generating answer..."
                        )


                        # ====================================
                        # AI ANSWER
                        # ====================================

                        evaluation = (
                            evaluate_answer(

                                st.session_state.question,

                                transcript,

                                role,

                                technologies,

                                experience
                            )
                        )


                        st.session_state.evaluation = (
                            evaluation
                        )


                        # ====================================
                        # SAVE HISTORY
                        # ====================================

                        st.session_state.history.append(

                            {

                                "question":
                                    st.session_state.question,

                                "candidate_answer":
                                    transcript,

                                "ai_answer":
                                    evaluation
                            }

                        )


                        # ====================================
                        # NEXT QUESTION TIMER
                        # ====================================

                        st.session_state.next_question_time = (

                            time.time()
                            +
                            wait_seconds

                        )


                        st.session_state.status = (

                            f"Answer generated. "
                            f"Next question in {wait_seconds} seconds."

                        )


                        st.rerun()


                except Exception as error:


                    st.session_state.status = (
                        "Voice processing error"
                    )


                    st.error(
                        error
                    )


    # --------------------------------------------------------
    # AUTOMATIC NEXT QUESTION
    # --------------------------------------------------------

    if (

        st.session_state.evaluation
        is not None

        and

        st.session_state.next_question_time
        > 0

        and

        time.time()
        >=
        st.session_state.next_question_time

    ):


        st.session_state.question = ""

        st.session_state.transcript = ""

        st.session_state.evaluation = None

        st.session_state.next_question_time = 0

        st.session_state.status = (
            "Preparing next question..."
        )


        st.rerun()


automatic_processing()


# ============================================================
# HISTORY
# ============================================================

st.divider()

st.subheader(
    "📚 Interview Practice History"
)


if st.session_state.history:


    scores = [

        item[
            "ai_answer"
        ].get(
            "score",
            0
        )

        for item
        in st.session_state.history

    ]


    average = (

        sum(scores)
        /
        len(scores)

    )


    st.metric(

        "Average Score",

        f"{average:.1f}/10"

    )


    for number, attempt in enumerate(

        reversed(
            st.session_state.history
        ),

        start=1
    ):


        with st.expander(

            f"Attempt {number}"

        ):


            st.write(
                "**Question:**"
            )


            st.write(
                attempt[
                    "question"
                ]
            )


            st.write(
                "**Your Spoken Answer:**"
            )


            st.write(
                attempt[
                    "candidate_answer"
                ]
            )


            st.write(
                "**Improved Humanized Answer:**"
            )


            st.write(

                attempt[
                    "ai_answer"
                ].get(
                    "humanized_answer",
                    ""
                )

            )


else:

    st.caption(
        "Your completed mock interview questions will appear here."
    )