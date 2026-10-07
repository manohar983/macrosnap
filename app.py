"""MacroSnap: a small Streamlit nutrition chat demo powered by Gemini and Twilio."""

from __future__ import annotations

import json
import re
from typing import Any, Optional

import streamlit as st
from google import genai
from google.genai import types
from twilio.rest import Client as TwilioClient

from prompts import NUTRITION_BUDDY_PROMPT, SUMMARY_PROMPT


st.set_page_config(page_title="MacroSnap · Nutrition buddy", page_icon="🥗", layout="wide")

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
      :root { --green: #36bd83; --deep: #e9f5ee; --mint: #183328; --ink: #e8f1eb; --muted: #b2c4b8; --panel: #14231b; --line: #31493a; }
      html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: var(--ink); }
      .stApp { background: radial-gradient(ellipse at 80% 0%, #183326 0%, transparent 42%), linear-gradient(135deg, #0b1510 0%, #101c15 55%, #0d1912 100%); color: var(--ink); }
      [data-testid="stHeader"] { background: rgba(11,21,16,.88); }
      .block-container { max-width: 1180px; padding-top: 2.1rem; padding-bottom: 3rem; }
      h1, h2, h3 { font-family: 'Manrope', sans-serif !important; letter-spacing: -0.035em; color: var(--deep); }
      [data-testid="stSidebar"] { background: #0c1811; border-right: 1px solid #25392d; }
      [data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }
      [data-testid="stSidebar"] *, .stApp, .stApp p, .stApp label, .stApp [data-testid="stMarkdownContainer"] { color: var(--ink); }
      [data-testid="stChatMessage"] { background: #15251c; border: 1px solid #304838; border-radius: 18px; padding: 1rem 1.1rem; box-shadow: 0 8px 24px rgba(0,0,0,.18); }
      [data-testid="stChatMessage"] p { line-height: 1.65; color: #e6f0e9; }
      div[data-testid="stForm"] { background: #14231b; border: 1px solid #31493a; border-radius: 20px; padding: 1rem; box-shadow: 0 12px 32px rgba(0,0,0,.2); }
      div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea { border-radius: 12px; background: #0e1a13; color: #f1f7f3; border-color: #496653; }
      div[data-testid="stTextInput"] input::placeholder, div[data-testid="stTextArea"] textarea::placeholder { color: #a9bcb0; opacity: 1; }
      div[data-testid="stFileUploader"] section { border-radius: 14px; background: #102019; border-color: #496653; }
      div[data-testid="stFileUploader"] section, div[data-testid="stFileUploader"] section * { color: #e6f0e9 !important; }
      div.stButton > button, div.stDownloadButton > button, div[data-testid="stFormSubmitButton"] button { border-radius: 12px; font-weight: 700; min-height: 2.7rem; transition: all .18s ease; background: #17281f; border-color: #3a5745; color: #edf6f0; }
      div.stButton > button:hover, div.stDownloadButton > button:hover { transform: translateY(-1px); border-color: #63c394; color: #9de4bd; }
      div[data-testid="stFormSubmitButton"] button[kind="primary"], div.stButton > button[kind="primary"] { background: #27a870; border-color: #27a870; color: #07150e; }
      .macro-hero { padding: 1.6rem 1.8rem; border-radius: 24px; background: radial-gradient(circle at 92% 15%, #d0e9d7 0, transparent 27%), linear-gradient(120deg, #153d2d, #176b4d); color: white; margin: .3rem 0 1.4rem; box-shadow: 0 16px 38px rgba(23,107,77,.16); }
      .macro-hero h1 { color: white !important; margin: .15rem 0 .35rem; font-size: 2.25rem; }
      .macro-hero p { color: #e0f1e5; margin: 0; font-size: 1rem; }
      .eyebrow { text-transform: uppercase; letter-spacing: .15em; font-size: .72rem; font-weight: 800; color: #a9d8b8; }
      .section-label { color: #a8c1b0; text-transform: uppercase; letter-spacing: .11em; font-size: .72rem; font-weight: 800; margin: .6rem 0 .35rem; }
      .status-card { background: #14231b; border: 1px solid #31493a; border-radius: 16px; padding: .9rem 1rem; margin: .5rem 0; }
      .status-line { display:flex; justify-content:space-between; gap:.5rem; padding:.24rem 0; color:#c4d4ca; font-size:.9rem; }
      .status-good { color:#7ee0a9; font-weight:700; }
      .status-needs { color:#ffd17a; font-weight:700; }
      .welcome-card { padding: 1rem 1.2rem; border: 1px solid #31493a; border-radius: 18px; background: rgba(20,35,27,.92); margin: .7rem 0 1rem; color: #edf6f0; }
      .welcome-card p { color: #bed0c4; margin: .15rem 0; }
      .stAlert { border-radius: 14px; }
      .stCaption, [data-testid="stCaptionContainer"] { color: #b3c5b9 !important; }
      [data-testid="stCheckbox"] label, [data-testid="stWidgetLabel"] p { color: #e4eee7 !important; }
      [data-testid="stExpander"] { background: #14231b; border: 1px solid #31493a; border-radius: 14px; }
      a { color: #8ae0b0 !important; }
      @media (max-width: 700px) { .block-container { padding: 1rem .9rem 2rem; } .macro-hero { padding: 1.2rem; } .macro-hero h1 { font-size:1.8rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)


def setting(name: str, default: str = "") -> str:
    """Read a setting from Streamlit secrets, falling back to an environment variable."""
    try:
        value = st.secrets.get(name, default)
    except (FileNotFoundError, KeyError):
        value = default
    return str(value or default).strip()


def api_client() -> genai.Client:
    key = setting("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Add GEMINI_API_KEY to .streamlit/secrets.toml first.")
    return genai.Client(api_key=key)


def ask_gemini(messages: list[dict[str, Any]], image: Optional[Any] = None) -> str:
    client = api_client()
    contents: list[Any] = []
    for message in messages[-12:]:
        role = "model" if message["role"] == "assistant" else "user"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=message["content"])]))
    if image is not None:
        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="Please estimate the meal in this photo. Identify visible foods, estimate portions, and give approximate calories and macros. Ask me a follow-up if needed."),
                    types.Part.from_bytes(data=image.getvalue(), mime_type=image.type),
                ],
            )
        )
    response = client.models.generate_content(
        model=setting("GEMINI_MODEL", "gemini-3.8-flash"),
        contents=contents,
        config=types.GenerateContentConfig(system_instruction=NUTRITION_BUDDY_PROMPT, temperature=0.4),
    )
    answer = (response.text or "").strip()
    if not answer:
        raise RuntimeError("Gemini returned an empty response. Please try again.")
    return answer


def create_summary(messages: list[dict[str, str]]) -> str:
    transcript = "\n".join(f"{item['role'].title()}: {item['content']}" for item in messages)
    client = api_client()
    response = client.models.generate_content(
        model=setting("GEMINI_MODEL", "gemini-3.8-flash"),
        contents=f"{SUMMARY_PROMPT}\n\nConversation:\n{transcript}",
        config=types.GenerateContentConfig(temperature=0.2),
    )
    summary = (response.text or "").strip()
    if not summary:
        raise RuntimeError("Gemini couldn't prepare the summary. Please try again.")
    return summary


def send_whatsapp(name: str, phone: str, summary: str) -> str:
    account_sid = setting("TWILIO_ACCOUNT_SID")
    auth_token = setting("TWILIO_AUTH_TOKEN")
    sender = setting("TWILIO_WHATSAPP_FROM")
    template_sid = setting("TWILIO_CONTENT_SID")
    if not all((account_sid, auth_token, sender)):
        raise RuntimeError("Complete the Twilio Account SID, Auth Token, and WhatsApp sender in .streamlit/secrets.toml first.")
    if not re.fullmatch(r"AC[0-9a-fA-F]{32}", account_sid):
        raise ValueError("TWILIO_ACCOUNT_SID must be your real 34-character Account SID starting with AC.")
    if template_sid and not re.fullmatch(r"HX[0-9a-fA-F]{32}", template_sid):
        raise ValueError("TWILIO_CONTENT_SID must be the real 34-character Content SID starting with HX.")
    if not re.fullmatch(r"\+[1-9]\d{7,14}", phone.strip()):
        raise ValueError("Enter a WhatsApp number in international format, such as +14155552671.")
    client = TwilioClient(account_sid, auth_token)
    message_args = {
        "from_": sender if sender.startswith("whatsapp:") else f"whatsapp:{sender}",
        "to": f"whatsapp:{phone.strip()}",
    }
    if template_sid:
        message_args["content_sid"] = template_sid
        message_args["content_variables"] = json.dumps({"1": name, "2": summary})
    else:
        # WhatsApp permits free-form replies inside the 24-hour customer-service window.
        message_args["body"] = f"Hi {name}, here's your MacroSnap conversation summary:\n\n{summary}"
    message = client.messages.create(**message_args)
    return message.sid


def profile_form() -> None:
    st.markdown(
        """
        <div class="macro-hero">
          <div class="eyebrow">Your everyday food companion</div>
          <h1>Eat curious. Feel good.</h1>
          <p>Snap a meal, ask a question, and get a friendly estimate of what’s on your plate.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### Let’s get your chat ready")
    st.markdown('<div class="welcome-card"><p>Your name and WhatsApp number are saved for this browser session. A summary is sent only when you choose to send it.</p></div>', unsafe_allow_html=True)
    with st.form("profile_form"):
        name = st.text_input("Your name", max_chars=60)
        phone = st.text_input("WhatsApp number", placeholder="+14155552671", help="Include + and your country code.")
        consent = st.checkbox("I agree that my chat summary will be sent to this WhatsApp number only when I press the send button.")
        submitted = st.form_submit_button("Start my nutrition chat →", type="primary", use_container_width=True)
    if submitted:
        if not name.strip() or not phone.strip():
            st.error("Please enter both your name and WhatsApp number.")
        elif not consent:
            st.error("Please confirm the WhatsApp summary consent to continue.")
        elif not re.fullmatch(r"\+[1-9]\d{7,14}", phone.strip()):
            st.error("Use international E.164 format, for example +14155552671.")
        else:
            st.session_state.user_profile = {"name": name.strip(), "phone": phone.strip()}
            st.session_state.messages = []
            st.rerun()


if "user_profile" not in st.session_state or "phone" not in st.session_state.user_profile:
    profile_form()
    st.stop()

profile = st.session_state.user_profile
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown("# 🥗 MacroSnap")
    st.caption("Your nutrition buddy")
    st.markdown(f"### Hey, {profile['name']} 👋")
    st.caption("A friendly place to explore meals and everyday nutrition.")
    st.markdown('<div class="section-label">Connections</div>', unsafe_allow_html=True)
    gemini_ready = bool(setting("GEMINI_API_KEY"))
    twilio_ready = bool(
        re.fullmatch(r"AC[0-9a-fA-F]{32}", setting("TWILIO_ACCOUNT_SID"))
        and setting("TWILIO_AUTH_TOKEN")
        and setting("TWILIO_WHATSAPP_FROM")
    )
    gemini_class = "status-good" if gemini_ready else "status-needs"
    twilio_class = "status-good" if twilio_ready else "status-needs"
    gemini_text = "Ready" if gemini_ready else "Add API key"
    twilio_text = "Ready" if twilio_ready else "Set up Twilio"
    st.markdown(
        f'<div class="status-card"><div class="status-line"><span>✨ Gemini AI</span><span class="{gemini_class}">{gemini_text}</span></div><div class="status-line"><span>💬 WhatsApp</span><span class="{twilio_class}">{twilio_text}</span></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-label">Your chat</div>', unsafe_allow_html=True)
    st.caption(f"{sum(1 for m in st.session_state.messages if m['role'] == 'user')} questions so far")
    if st.button("＋ Start a fresh chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    if st.button("Edit my profile", use_container_width=True):
        del st.session_state.user_profile
        st.rerun()
    st.divider()
    st.caption("Nutrition estimates are approximate and are not medical advice.")

st.markdown(
    f"""
    <div class="macro-hero">
      <div class="eyebrow">MACRO SNAP · FOOD, MADE SIMPLE</div>
      <h1>What’s on your plate, {profile['name']}?</h1>
      <p>Ask a question or add a photo. We’ll explore the meal together.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.messages:
    st.markdown('<div class="welcome-card"><strong>Start anywhere.</strong><p>Pick a starter below, type your own question, or upload a meal photo.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Quick starters</div>', unsafe_allow_html=True)
    starter_columns = st.columns(3)
    starters = [
        ("🥗 Estimate a meal", "Estimate calories and macros for this meal: "),
        ("🍳 Build a balanced plate", "How can I make my next meal more balanced?"),
        ("💪 Protein ideas", "Suggest a few simple high-protein snack ideas."),
    ]
    for col, (label, text) in zip(starter_columns, starters):
        with col:
            if st.button(label, use_container_width=True, key=f"starter_{label}"):
                st.session_state.chat_prompt = text
                st.rerun()
else:
    st.markdown('<div class="section-label">Your conversation</div>', unsafe_allow_html=True)

for item in st.session_state.messages:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

with st.form("chat", clear_on_submit=True):
    prompt = st.text_input("Ask your nutrition buddy", placeholder="What are the macros in a bowl of dal and rice?", key="chat_prompt")
    photo = st.file_uploader("Add a meal photo (optional)", type=["jpg", "jpeg", "png", "webp"], help="JPG, PNG or WEBP")
    submitted = st.form_submit_button("Send to MacroSnap  →", type="primary", use_container_width=True)

if submitted:
    if not prompt.strip() and photo is None:
        st.warning("Type a question or attach a meal photo first.")
    else:
        user_text = prompt.strip() or "Please estimate this meal from the photo."
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)
            if photo is not None:
                st.image(photo, caption=photo.name, width=300)
        with st.chat_message("assistant"):
            with st.spinner("Thinking about your meal…"):
                try:
                    answer = ask_gemini(st.session_state.messages[:-1] + [{"role": "user", "content": user_text}], photo)
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as exc:
                    st.error(f"I couldn't get a response: {exc}")
                    st.session_state.messages.pop()

summary_lines = [
    f"MacroSnap conversation summary for {profile['name']}",
    "Nutrition estimates are approximate and not medical advice.",
    "",
]
summary_lines.extend(f"{item['role'].title()}: {item['content']}" for item in st.session_state.messages)
action_left, action_right = st.columns(2)
with action_left:
    if st.button("💬 Send summary to WhatsApp", type="primary", use_container_width=True, disabled=not st.session_state.messages):
        with st.spinner("Putting your summary together…"):
            try:
                summary = create_summary(st.session_state.messages)
                sid = send_whatsapp(profile["name"], profile["phone"], summary)
                st.success(f"Summary sent to {profile['phone']}.")
            except Exception as exc:
                if getattr(exc, "code", None) == 63016 and not setting("TWILIO_CONTENT_SID"):
                    st.error("The WhatsApp 24-hour reply window is closed. From the recipient's WhatsApp, send a new message to your Twilio sandbox number, then retry.")
                else:
                    st.error(f"Couldn't send the WhatsApp summary: {exc}")
with action_right:
    st.download_button(
        "↓ Download chat summary",
        data="\n".join(summary_lines),
        file_name="macrosnap_summary.txt",
        mime="text/plain",
        disabled=not st.session_state.messages,
        use_container_width=True,
        help="Save a text copy of this chat to your device.",
    )

if not setting("TWILIO_CONTENT_SID"):
    st.caption("Sandbox mode: from the recipient's WhatsApp, message your Twilio sandbox number within the last 24 hours before sending the summary. A custom template SID is optional during that window.")
