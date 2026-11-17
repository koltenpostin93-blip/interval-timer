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


# Phones only allow sound that was "unlocked" by a tap, and the timer's beeps fire
# later from a timer, not from a tap. So the first tap (Start) unlocks WebAudio +
# speech once, and every later cue plays through that unlocked audio context.
SETUP_JS = """<script>(()=>{
if(window.__jsa)return;const J=window.__jsa={ctx:null};
const unlock=()=>{
 try{const AC=window.AudioContext||window.webkitAudioContext;J.ctx=J.ctx||new AC();J.ctx.resume();
  const s=J.ctx.createBufferSource();s.buffer=J.ctx.createBuffer(1,1,22050);s.connect(J.ctx.destination);s.start(0);}catch(e){}
 try{const u=new SpeechSynthesisUtterance(' ');u.volume=0;speechSynthesis.speak(u);}catch(e){}
 try{navigator.wakeLock&&navigator.wakeLock.request('screen').catch(()=>{});}catch(e){}
};
['pointerdown','touchend','click','keydown'].forEach(ev=>document.addEventListener(ev,unlock,{capture:true,passive:true}));
J.cue=(freq,dur,text)=>{
 try{const c=J.ctx;if(c){if(c.state!=='running')c.resume();
  const o=c.createOscillator(),g=c.createGain();o.frequency.value=freq;
  g.gain.setValueAtTime(0.7,c.currentTime);g.gain.linearRampToValueAtTime(0,c.currentTime+dur);
  o.connect(g);g.connect(c.destination);o.start();o.stop(c.currentTime+dur);}}catch(e){}
 setTimeout(()=>{try{speechSynthesis.cancel();speechSynthesis.speak(new SpeechSynthesisUtterance(text));}catch(e){}},dur*1000+150);
};})();</script>"""
st.html(SETUP_JS, unsafe_allow_javascript=True)


def cue(freq, secs, text):
    """Beep (freq Hz for secs seconds), then say text out loud."""
    import json

    st.html(
        f"<script>window.__jsa&&window.__jsa.cue({freq},{secs},{json.dumps(text)})</script>",
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
            freq, secs = 880, 0.9  # long beep
        else:
            say = f"Time to {b_name.lower()}"
            freq, secs = 600, 0.3  # short, lower beep
        cue(freq, secs, say)
    name, length, into = (a_name, a_sec, pos) if in_a else (b_name, b_sec, pos - a_sec)
    st.markdown(f"<h1 style='text-align:center;font-size:5rem;margin:0'>{fmt(length - into + 0.99)}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center;margin:0'>{name}</h2>", unsafe_allow_html=True)
    st.progress(min(into / length, 1.0))
    st.caption(f"Round {int(elapsed // cycle) + 1} · {fmt(total - elapsed + 0.99)} left overall")


display()
if ss.pop("finished", False):
    st.success("Done!")
    cue(1200, 0.8, "Done")
