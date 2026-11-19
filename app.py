import html
import re
from datetime import datetime

import streamlit as st

from backend.ingest import build_index
from backend.rag import answer_question
from backend.handoff import (TIME_SLOTS, TOPICS, confirmation_message, handoff_message,
                             save_request, valid_phone, wants_human)

st.set_page_config(page_title="ShopEasy Support", page_icon="🛍️",
                   layout="centered", initial_sidebar_state="expanded")

CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root{--primary:#4F46E5;--ink:#0F172A;--muted:#64748B;--line:#E2E8F0;}
html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], .stMarkdown, .stButton button, [data-testid="stChatInput"] textarea{font-family:'Inter',system-ui,sans-serif !important;}
[data-testid="stAppViewContainer"]{background:linear-gradient(180deg,#F8FAFC 0%,#EEF2FF 100%);}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stToolbar"]{visibility:hidden;}
[data-testid="stSidebar"]{background:#FFFFFF;border-right:1px solid var(--line);}
footer{visibility:hidden;}
.block-container{max-width:860px;padding-top:2rem;padding-bottom:7rem;}
.hero{background:linear-gradient(135deg,#312E81 0%,#4F46E5 55%,#0EA5E9 130%);border-radius:20px;padding:24px 28px;color:#fff;box-shadow:0 12px 30px rgba(79,70,229,.25);margin-bottom:22px;}
.hero-top{display:flex;align-items:center;gap:16px;}
.logo{width:52px;height:52px;border-radius:14px;background:rgba(255,255,255,.18);display:flex;align-items:center;justify-content:center;font-size:26px;flex:none;}
.hero-title{font-size:1.55rem;font-weight:700;line-height:1.2;}
.hero-sub{opacity:.88;font-size:.95rem;margin-top:3px;}
.status{margin-left:auto;display:flex;align-items:center;gap:8px;background:rgba(255,255,255,.16);padding:6px 12px;border-radius:999px;font-size:.8rem;font-weight:600;}
.dot{width:8px;height:8px;border-radius:50%;background:#34D399;box-shadow:0 0 0 4px rgba(52,211,153,.25);}
.pills{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px;}
.pill{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);padding:5px 12px;border-radius:999px;font-size:.8rem;}
.welcome{background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px 22px;margin-bottom:18px;box-shadow:0 2px 10px rgba(15,23,42,.04);}
.welcome h3{margin:0 0 6px 0;font-size:1.1rem;color:var(--ink);}
.welcome p{margin:0;color:var(--muted);font-size:.93rem;line-height:1.55;}
.section-label{font-size:.74rem;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);margin:6px 0 10px 2px;}
.stButton>button{border-radius:12px;border:1px solid var(--line);background:#fff;color:var(--ink);padding:.7rem 1rem;font-weight:500;justify-content:flex-start;box-shadow:0 1px 3px rgba(15,23,42,.05);transition:all .15s ease;}
.stButton>button:hover{border-color:var(--primary);color:var(--primary);transform:translateY(-1px);box-shadow:0 6px 16px rgba(79,70,229,.12);}
.row{display:flex;gap:12px;margin:14px 0;align-items:flex-end;}
.row.user{justify-content:flex-end;}
.msg{max-width:78%;display:flex;flex-direction:column;}
.row.user .msg{align-items:flex-end;}
.bubble{padding:12px 16px;font-size:.95rem;line-height:1.6;word-wrap:break-word;}
.user-b{background:linear-gradient(135deg,#4F46E5,#6366F1);color:#fff;border-radius:18px 18px 4px 18px;box-shadow:0 6px 16px rgba(79,70,229,.25);}
.bot-b{background:#fff;color:var(--ink);border:1px solid var(--line);border-radius:18px 18px 18px 4px;box-shadow:0 2px 10px rgba(15,23,42,.05);}
.meta{font-size:.72rem;color:var(--muted);margin:5px 6px 0 6px;}
.avatar{width:36px;height:36px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;font-size:.72rem;font-weight:700;}
.user-a{background:#E0E7FF;color:#3730A3;}
.bot-a{background:#fff;border:1px solid var(--line);font-size:18px;}
.chips-src{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 0 2px;}
.src{background:#EEF2FF;color:#3730A3;border:1px solid #C7D2FE;border-radius:999px;padding:3px 10px;font-size:.74rem;font-weight:500;}
.typing{display:inline-flex;gap:5px;padding:4px 2px;}
.typing span{width:8px;height:8px;border-radius:50%;background:#94A3B8;animation:blink 1.2s infinite ease-in-out;}
.typing span:nth-child(2){animation-delay:.2s;}
.typing span:nth-child(3){animation-delay:.4s;}
@keyframes blink{0%,80%,100%{opacity:.3;transform:translateY(0);}40%{opacity:1;transform:translateY(-3px);}}
[data-testid="stBottom"], [data-testid="stBottom"] > div{background:transparent !important;}
[data-testid="stChatInput"]{border-radius:16px;border:1px solid var(--line);background:#fff;box-shadow:0 8px 24px rgba(15,23,42,.08);}
.side-card{text-align:center;padding:6px 0 14px 0;}
.side-logo{width:60px;height:60px;margin:0 auto 10px auto;border-radius:16px;background:linear-gradient(135deg,#4F46E5,#0EA5E9);display:flex;align-items:center;justify-content:center;font-size:30px;box-shadow:0 8px 20px rgba(79,70,229,.25);}
.side-title{font-weight:700;font-size:1.15rem;color:var(--ink);}
.side-sub{color:var(--muted);font-size:.85rem;}
.topic{background:#F1F5F9;border-radius:10px;padding:8px 12px;margin-bottom:8px;font-size:.88rem;color:var(--ink);}
.side-note{color:var(--muted);font-size:.78rem;line-height:1.5;margin-top:12px;}
.form-title{font-weight:700;font-size:1.05rem;color:var(--ink);margin-bottom:2px;}
.form-sub{color:var(--muted);font-size:.85rem;margin-bottom:6px;}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px;background:#fff;}
@media (max-width:640px){.msg{max-width:88%;}.status{display:none;}.hero{padding:18px;}.hero-title{font-size:1.3rem;}}
</style>"""

HERO = '<div class="hero"><div class="hero-top"><div class="logo">&#128717;</div><div><div class="hero-title">ShopEasy Support</div><div class="hero-sub">Ask about orders, refunds, shipping and warranty</div></div><div class="status"><span class="dot"></span>Online</div></div><div class="pills"><span class="pill">&#9889; Instant answers</span><span class="pill">&#128196; Cites its sources</span><span class="pill">&#128274; Company documents only</span></div></div>'

WELCOME = '<div class="welcome"><h3>Hi there, how can I help?</h3><p>I am ShopEasy\'s virtual assistant. I answer only from our official support documents, so you always get consistent, sourced information.</p></div><div class="section-label">Popular questions</div>'

SIDEBAR = '<div class="side-card"><div class="side-logo">&#128717;</div><div class="side-title">ShopEasy</div><div class="side-sub">Customer Support Assistant</div></div><div class="section-label">I can help with</div><div class="topic">&#8617;&#65039; Returns &amp; refunds</div><div class="topic">&#128666; Shipping &amp; delivery</div><div class="topic">&#128737;&#65039; Warranty claims</div><div class="topic">&#128222; Contact &amp; support hours</div><div class="side-note">Answers come only from official support documents. Built with RAG, ChromaDB and Gemini.</div>'

TYPING = '<div class="row bot"><div class="avatar bot-a">&#128717;</div><div class="msg"><div class="bubble bot-b"><div class="typing"><span></span><span></span><span></span></div></div></div></div>'

EXAMPLES = [
    (":material/keyboard_return:", "What is your return policy?"),
    (":material/local_shipping:", "How long does shipping take?"),
    (":material/verified_user:", "Is there a warranty on electronics?"),
    (":material/schedule:", "What are your support hours?"),
]

st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading support documents...")
def load_index():
    return build_index()


collection = load_index()
ss = st.session_state
ss.setdefault("messages", [])
ss.setdefault("pending", False)
ss.setdefault("form_open", False)


def now():
    return datetime.now().strftime("%I:%M %p").lstrip("0")


def fmt(text):
    safe = html.escape(text)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
    safe = re.sub(r"(?m)^\s*[-*]\s+", "&bull; ", safe)
    return safe.replace("\n", "<br>")


def pretty(filename):
    return filename.replace(".txt", "").replace("_", " ").title()


def bubble(role, text, time_str, sources=None):
    body = fmt(text)
    if role == "user":
        return (f'<div class="row user"><div class="msg"><div class="bubble user-b">{body}</div>'
                f'<div class="meta">You &middot; {time_str}</div></div>'
                f'<div class="avatar user-a">You</div></div>')
    chips = ""
    if sources:
        items = "".join(f'<span class="src">&#128196; {html.escape(pretty(s))}</span>'
                        for s in sources)
        chips = f'<div class="chips-src">{items}</div>'
    return (f'<div class="row bot"><div class="avatar bot-a">&#128717;</div><div class="msg">'
            f'<div class="bubble bot-b">{body}</div>{chips}'
            f'<div class="meta">ShopEasy Assistant &middot; {time_str}</div></div></div>')


def bot_say(text):
    ss.messages.append({"role": "assistant", "content": text, "sources": [],
                        "debug": [], "time": now()})


def ask(question):
    ss.messages.append({"role": "user", "content": question, "time": now()})
    if wants_human(question):          # customer wants a call or a person
        bot_say(handoff_message())
        ss.form_open = True
    else:
        ss.pending = True


# ---------- sidebar ----------
with st.sidebar:
    st.markdown(SIDEBAR, unsafe_allow_html=True)
    st.button("Talk to an executive", icon=":material/call:", type="primary",
              use_container_width=True, on_click=ask,
              args=("I would like to talk to an executive",))
    show_debug = st.toggle("Show retrieved chunks")
    if st.button("Clear conversation", icon=":material/delete:", use_container_width=True):
        ss.messages = []
        ss.pending = False
        ss.form_open = False
        st.rerun()

# ---------- input ----------
typed = st.chat_input("Ask about orders, refunds, shipping or warranty...")
if typed:
    ask(typed)
    st.rerun()

# ---------- main page ----------
st.markdown(HERO, unsafe_allow_html=True)

if not ss.messages:
    st.markdown(WELCOME, unsafe_allow_html=True)
    cols = st.columns(2)
    for i, (icon, q) in enumerate(EXAMPLES):
        cols[i % 2].button(q, icon=icon, key=f"ex{i}", use_container_width=True,
                           on_click=ask, args=(q,))

for m in ss.messages:
    st.markdown(bubble(m["role"], m["content"], m["time"], m.get("sources")),
                unsafe_allow_html=True)
    if show_debug and m.get("debug"):
        with st.expander("Retrieved chunks"):
            for h in m["debug"]:
                st.write(f"{h['source']} - distance {h['distance']:.2f}")
                st.text(h["text"])

if ss.form_open:
    with st.container(border=True):
        st.markdown('<div class="form-title">&#128222; Request a callback</div>'
                    '<div class="form-sub">A support executive will call you back. '
                    'We only use these details to contact you about this request.</div>',
                    unsafe_allow_html=True)
        with st.form("callback_form", border=False):
            name = st.text_input("Your name")
            phone = st.text_input("Phone number", placeholder="e.g. 9876543210")
            c1, c2 = st.columns(2)
            topic = c1.selectbox("Topic", TOPICS)
            slot = c2.selectbox("Preferred time", TIME_SLOTS)
            b1, b2 = st.columns(2)
            submitted = b1.form_submit_button("Request a call", type="primary",
                                              use_container_width=True)
            cancelled = b2.form_submit_button("Not now", use_container_width=True)

    if cancelled:
        ss.form_open = False
        bot_say("No problem. Let me know if there is anything else I can help with.")
        st.rerun()
    if submitted:
        if not name.strip():
            st.error("Please enter your name.")
        elif not valid_phone(phone):
            st.error("Please enter a valid phone number (8 to 15 digits).")
        else:
            ticket = save_request(name, phone, topic, slot)
            ss.form_open = False
            bot_say(confirmation_message(name, phone, slot, ticket))
            st.rerun()

if ss.pending:
    st.markdown(TYPING, unsafe_allow_html=True)
    history = [(m["role"], m["content"]) for m in ss.messages[:-1]]
    result = answer_question(collection, ss.messages[-1]["content"], history)
    ss.messages.append({"role": "assistant", "content": result["answer"],
                        "sources": result["sources"], "debug": result["debug"],
                        "time": now()})
    ss.pending = False
    st.rerun()