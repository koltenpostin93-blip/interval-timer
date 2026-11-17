import time

import streamlit as st

st.set_page_config(page_title="Interval timer", page_icon=":material/timer:")
st.title("Interval timer")

ss = st.session_state
ss.setdefault("start", None)  # time.time() when started, None when stopped
running = ss.start is not None

with st.container(border=True):
    c1, c2 = st.columns(2)
    a_name = c1.text_input("Interval A name", "Work", disabled=running)
    a_sec = c1.number_input("Interval A (seconds)", 1, 7200, 30, step=5, disabled=running)
    b_name = c2.text_input("Interval B name", "Rest", disabled=running)
    b_sec = c2.number_input("Interval B (seconds)", 1, 7200, 10, step=5, disabled=running)

    mode = st.segmented_control(
        "Repeat for", ["Number of rounds", "Total time"], default="Number of rounds", disabled=running
    )
    if mode == "Total time":
        total = st.number_input("Total time (minutes)", 1, 600, 20) * 60
    else:
        rounds = st.number_input("Rounds (A + B each)", 1, 500, 8, disabled=running)
        total = rounds * (a_sec + b_sec)

cycle = a_sec + b_sec

if running:
    if st.button("Stop", type="primary", icon=":material/stop:", width="stretch"):
        ss.start = None
        st.rerun()
else:
    if st.button("Start", type="primary", icon=":material/play_arrow:", width="stretch"):
        ss.start = time.time()
        ss.last_idx = None
        st.rerun()


@st.cache_data
def beep_wav(freq=880, secs=0.4, rate=22050):
    import io, math, struct, wave

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        n = int(rate * secs)
        w.writeframes(b"".join(
            struct.pack("<h", int(20000 * math.sin(2 * math.pi * freq * i / rate) * (1 - i / n)))
            for i in range(n)
        ))
    return buf.getvalue()


def speak(text):
    """Say text out loud with the browser's built-in voice, just after the beep."""
    import json

    st.html(
        f"<script>setTimeout(()=>{{const u=new SpeechSynthesisUtterance({json.dumps(text)});"
        "speechSynthesis.cancel();speechSynthesis.speak(u);}, 700);</script>",
        unsafe_allow_javascript=True,
    )


def fmt(s):
    s = int(s)
    return f"{s // 60}:{s % 60:02d}"


@st.fragment(run_every=1 if running else None)
def display():
    if ss.start is None:
        st.caption(f"Total length: {fmt(total)}")
        return
    elapsed = time.time() - ss.start
    if elapsed >= total:
        ss.start = None
        ss.finished = True
        st.rerun()  # full rerun to re-enable the inputs
    pos = elapsed % cycle
    in_a = pos < a_sec
    idx = int(elapsed // cycle) * 2 + (0 if in_a else 1)
    if idx != ss.get("last_idx"):
        ss.last_idx = idx
        if in_a:
            say = f"Start {a_name.lower()}" if idx == 0 else f"Back to {a_name.lower()}"
            st.audio(beep_wav(880, 0.9), format="audio/wav", autoplay=True, width=1)  # long beep
        else:
            say = f"Time to {b_name.lower()}"
            st.audio(beep_wav(600, 0.3), format="audio/wav", autoplay=True, width=1)  # short, lower beep
        speak(say)
    name, length, into = (a_name, a_sec, pos) if in_a else (b_name, b_sec, pos - a_sec)
    st.markdown(f"<h1 style='text-align:center;font-size:5rem;margin:0'>{fmt(length - into + 0.99)}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center;margin:0'>{name}</h2>", unsafe_allow_html=True)
    st.progress(min(into / length, 1.0))
    st.caption(f"Round {int(elapsed // cycle) + 1} · {fmt(total - elapsed + 0.99)} left overall")


display()
if ss.pop("finished", False):
    st.success("Done!")
    st.audio(beep_wav(1200, 0.8), format="audio/wav", autoplay=True, width=1)
    speak("Done")
