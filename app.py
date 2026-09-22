"""
app.py - Professional Quran Study Companion Dashboard
"""
import streamlit as st
from config import APP_NAME, APP_TAGLINE, APP_ICON, DAILY_GOAL_POINTS
from utils.helpers import inject_css, page_header, compute_streak
from database import db
from services import quran_api

st.set_page_config(
    page_title=f"{APP_NAME} — Dashboard", 
    page_icon=APP_ICON, 
    layout="wide",
    initial_sidebar_state="expanded"
)

db.init_db()
inject_css()

# Custom CSS for animations and professional look
st.markdown("""
<style>
/* Smooth fade-in animation */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(-30px); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}

/* Apply animations */
.qsc-card {
    animation: fadeIn 0.8s ease-out;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.qsc-card:hover {
    transform: translateY(-5px) scale(1.02);
    box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 40px rgba(46,204,113,0.2);
}

.qsc-stat {
    animation: fadeIn 0.6s ease-out;
    transition: all 0.3s ease;
}

.qsc-stat:hover {
    transform: translateY(-8px);
    box-shadow: 0 15px 40px rgba(46,204,113,0.3);
}

/* Gradient text effect */
.gradient-text {
    background: linear-gradient(135deg, #2ecc71 0%, #d4af37 50%, #2ecc71 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    background-size: 200% auto;
    animation: shimmer 3s linear infinite;
}

/* Glowing effect for buttons */
.stButton>button {
    position: relative;
    overflow: hidden;
    transition: all 0.4s ease;
}

.stButton>button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    transition: left 0.5s;
}

.stButton>button:hover::before {
    left: 100%;
}

/* Animated background gradient */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(-45deg, #04120c, #0b2e22, #0f2c22, #123527);
    background-size: 400% 400%;
    animation: gradientShift 15s ease infinite;
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Progress bar animation */
.stProgress > div > div {
    background: linear-gradient(90deg, #2ecc71, #d4af37, #2ecc71);
    background-size: 200% 100%;
    animation: shimmer 2s linear infinite;
}

/* Smooth scroll behavior */
html {
    scroll-behavior: smooth;
}

/* Card border glow on hover */
.qsc-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 22px;
    padding: 2px;
    background: linear-gradient(135deg, #d4af37, #2ecc71, #d4af37);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    opacity: 0;
    transition: opacity 0.4s ease;
}

.qsc-card:hover::before {
    opacity: 1;
}
</style>
""", unsafe_allow_html=True)

# Sidebar with enhanced branding
with st.sidebar:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:30px;padding:20px;background:linear-gradient(135deg, rgba(46,204,113,0.1), rgba(212,175,55,0.1));border-radius:16px;border:1px solid rgba(212,175,55,0.2);">
        <div style="font-size:2.5rem;animation:pulse 2s infinite;">{APP_ICON}</div>
        <div>
            <div style="font-weight:700;font-size:1.2rem;color:#f4f7f5;letter-spacing:-0.5px;">{APP_NAME}</div>
            <div style="font-size:0.85rem;color:#7e9186;margin-top:2px;">{APP_TAGLINE}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='border:none;border-top:1px solid rgba(212,175,55,0.2);margin:20px 0;'>", unsafe_allow_html=True)

# Main header with animated elements
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.markdown(f"""
    <div style="width:70px;height:70px;background:linear-gradient(135deg, #2ecc71, #d4af37);border-radius:20px;display:flex;align-items:center;justify-content:center;font-size:2.5rem;box-shadow:0 10px 30px rgba(46,204,113,0.4);animation:slideIn 0.8s ease-out;">
        {APP_ICON}
    </div>
    """, unsafe_allow_html=True)
with col_title:
    st.markdown(f"""
    <div style="animation:fadeIn 1s ease-out;">
        <h1 style="margin:0;font-size:2.5rem;background:linear-gradient(135deg, #2ecc71, #d4af37);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Dashboard</h1>
        <p style="color:#7e9186;margin:5px 0 0 0;font-size:1.1rem;">Welcome back — here's your study space for today.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

# Search bar with enhanced styling
search_col1, search_col2 = st.columns([3, 1])
with search_col1:
    quick_q = st.text_input(
        "Search", 
        placeholder="✨ Search or ask AI (e.g., 'Al-Fatiha tafsir', 'Surah 2:255')",
        label_visibility="collapsed",
        help="Type your question about Quran, Hadith, or Islamic topics"
    )
    if quick_q:
        st.session_state["prefill_chat_question"] = quick_q
        st.success("✅ Question ready! Open **AI Companion** in the sidebar to get answers.")

# Stats with animations
completion_dates = db.get_all_completion_dates()
streak = compute_streak(completion_dates)
total_points = db.get_total_points()
points_today = db.get_points_today()
goals_today = db.get_goals_for_date()
done_today = sum(1 for g in goals_today if g["is_done"])

st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)
st.markdown("<h2 style='color:#d4af37;margin-bottom:20px;'>📊 Your Progress</h2>", unsafe_allow_html=True)

s1, s2, s3, s4 = st.columns(4)
stats = [
    (s1, "🔥", streak, "Day Streak", "Keep it up!"),
    (s2, "⭐", total_points, "Total Points", "All time"),
    (s3, "✅", f"{done_today}/{len(goals_today)}", "Goals Today", "Progress"),
    (s4, "➕", points_today, "Points Today", "Earned"),
]

for idx, (col, emoji, value, label, subtitle) in enumerate(stats):
    with col:
        st.markdown(f"""
        <div class="qsc-stat" style="animation-delay:{idx*0.1}s;">
            <div style="font-size:2.5rem;margin-bottom:10px;">{emoji}</div>
            <div style="font-size:2rem;font-weight:700;color:#2ecc71;line-height:1;">{value}</div>
            <div style="color:#d4af37;font-weight:600;margin-top:5px;font-size:0.9rem;">{label}</div>
            <div style="color:#7e9186;font-size:0.75rem;margin-top:3px;">{subtitle}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:50px;'></div>", unsafe_allow_html=True)

# Verse of the Day with enhanced design
st.markdown("<h2 style='color:#2ecc71;margin-bottom:20px;'>📖 Verse of the Day</h2>", unsafe_allow_html=True)

with st.spinner("✨ Loading today's verse..."):
    try:
        verse = quran_api.get_verse_of_the_day()
        
        st.markdown(f'''
        <div class="qsc-card" style="position:relative;overflow:hidden;">
            <div style="position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,#2ecc71,#d4af37,#2ecc71);background-size:200% 100%;animation:shimmer 3s linear infinite;"></div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:25px;">
                <span style="color:#7e9186;text-transform:uppercase;letter-spacing:2px;font-size:0.85rem;font-weight:600;">Daily Inspiration</span>
                <span style="background:linear-gradient(135deg,rgba(212,175,55,0.2),rgba(46,204,113,0.2));color:#d4af37;padding:8px 16px;border-radius:20px;font-weight:600;border:1px solid rgba(212,175,55,0.3);">{verse.get('label','')}</span>
            </div>
        ''', unsafe_allow_html=True)
        
        if verse.get("arabic"):
            st.markdown(f'''
            <div style="background:linear-gradient(135deg,rgba(15,44,34,0.8),rgba(18,53,39,0.8));padding:30px;border-radius:16px;margin:20px 0;border:1px solid rgba(212,175,55,0.2);">
                <div class="arabic-text" style="font-size:2rem;line-height:3;text-align:center;color:#f4f7f5;">
                    {verse["arabic"]}
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        if verse.get("transliteration"):
            st.markdown(f'<p style="color:#b9c9c0;font-style:italic;text-align:center;font-size:1.1rem;margin:20px 0;">{verse["transliteration"]}</p>', unsafe_allow_html=True)
        
        if verse.get("english"):
            st.markdown(f'''
            <div style="background:rgba(46,204,113,0.05);padding:25px;border-radius:16px;border-left:4px solid #2ecc71;margin:20px 0;">
                <p style="color:#f4f7f5;line-height:1.8;font-size:1.05rem;">{verse["english"]}</p>
            </div>
            ''', unsafe_allow_html=True)
        
        with st.expander("🇵🇰 اردو ترجمہ (Urdu Translation)", expanded=False):
            if verse.get("urdu"):
                st.markdown(f'<div class="urdu-text" style="font-size:1.3rem;line-height:2.5;text-align:right;padding:20px;background:rgba(212,175,55,0.05);border-radius:12px;border-right:4px solid #d4af37;">{verse["urdu"]}</div>', unsafe_allow_html=True)
        
        colA, colB, colC = st.columns([1, 2, 1])
        with colB:
            if st.button("➕ Add to Today's Goals", use_container_width=True, type="primary"):
                db.add_goal("memorize_verse", f"Learn {verse.get('label')}", DAILY_GOAL_POINTS["memorize_verse"])
                st.balloons()
                st.success("✅ Added to today's goals! Keep going! 🎯")
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"️ Couldn't load the verse. Please check your internet connection. ({str(e)})")

# Daily Goals Section
st.markdown("<div style='height:50px;'></div>", unsafe_allow_html=True)
st.markdown("<h2 style='color:#d4af37;margin-bottom:20px;'>🎯 Today's Goals</h2>", unsafe_allow_html=True)

st.markdown('<div class="qsc-card">', unsafe_allow_html=True)

with st.form("add_goal_form", clear_on_submit=True, border=False):
    st.markdown("<p style='color:#7e9186;margin-bottom:15px;'>Add a new learning goal for today:</p>", unsafe_allow_html=True)
    gcol1, gcol2 = st.columns([4, 1])
    with gcol1:
        goal_desc = st.text_input(
            "New Goal", 
            placeholder="e.g., Learn Surah Al-Asr, Listen to Surah Yasin, Read 5 pages...",
            label_visibility="collapsed"
        )
    with gcol2:
        submitted = st.form_submit_button("➕ Add Goal", use_container_width=True, type="secondary")
    if submitted and goal_desc.strip():
        db.add_goal("custom", goal_desc.strip(), DAILY_GOAL_POINTS["custom"])
        st.balloons()
        st.rerun()

if not goals_today:
    st.markdown("""
    <div style="text-align:center;padding:40px;background:rgba(46,204,113,0.05);border-radius:12px;border:2px dashed rgba(46,204,113,0.3);">
        <div style="font-size:3rem;margin-bottom:15px;">🎯</div>
        <p style="color:#7e9186;font-size:1.1rem;">No goals yet today — start your journey by adding one above!</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    
    for idx, g in enumerate(goals_today):
        gc1, gc2, gc3 = st.columns([0.5, 5, 1.5])
        with gc1:
            checked = st.checkbox("", value=bool(g["is_done"]), key=f"goal_{g['id']}", label_visibility="collapsed")
            if checked != bool(g["is_done"]):
                db.toggle_goal(g["id"], checked)
                if checked:
                    st.toast(f"🎉 Goal completed! +{g['points']} points!", icon="✅")
                st.rerun()
        
        with gc2:
            if g["is_done"]:
                st.markdown(f'<span style="text-decoration:line-through;color:#7e9186;font-size:1.05rem;">✅ {g["description"]}</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span style="color:#f4f7f5;font-size:1.05rem;">⬜ {g["description"]}</span>', unsafe_allow_html=True)
        
        with gc3:
            st.markdown(f'<span style="background:linear-gradient(135deg,#2ecc71,#d4af37);color:#04120c;padding:6px 12px;border-radius:12px;font-weight:700;font-size:0.9rem;">+{g["points"]} pts</span>', unsafe_allow_html=True)
    
    # Progress bar
    progress = done_today / max(1, len(goals_today))
    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
    st.progress(progress)
    st.markdown(f"""
    <div style="text-align:center;margin-top:10px;">
        <span style="color:{'#2ecc71' if progress >= 0.5 else '#d4af37'};font-weight:600;font-size:1.1rem;">
            {done_today} of {len(goals_today)} goals complete ({int(progress*100)}%)
        </span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Quick Access Cards
st.markdown("<div style='height:50px;'></div>", unsafe_allow_html=True)
st.markdown("<h2 style='color:#2ecc71;margin-bottom:20px;'>🚀 Quick Access</h2>", unsafe_allow_html=True)

l1, l2, l3 = st.columns(3)

quick_links = [
    ("📖", "Browse Quran", "Read every surah with audio & translation", "pages/1_📖_Browse_Quran.py"),
    ("🤖", "AI Companion", "Ask about verses, hadith, or any topic", "pages/2_🤖_AI_Companion.py"),
    ("🎙️", "Recitation Coach", "Practice & get pronunciation feedback", "pages/3_🎙️_Recitation_Coach.py"),
]

for idx, (emoji, title, desc, _) in enumerate(quick_links):
    with [l1, l2, l3][idx]:
        st.markdown(f"""
        <div class="qsc-card qsc-card-tight" style="text-align:center;cursor:pointer;animation-delay:{idx*0.1}s;">
            <div style="font-size:3rem;margin-bottom:15px;animation:pulse 2s infinite;">{emoji}</div>
            <h3 style="color:#d4af37;margin:10px 0;font-size:1.2rem;">{title}</h3>
            <p style="color:#7e9186;font-size:0.9rem;line-height:1.6;">{desc}</p>
            <div style="margin-top:15px;padding:8px 16px;background:linear-gradient(135deg,rgba(46,204,113,0.2),rgba(212,175,55,0.2));border-radius:20px;color:#2ecc71;font-weight:600;font-size:0.85rem;">
                Click to open →
            </div>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;padding:30px;background:rgba(15,44,34,0.5);border-radius:16px;border-top:1px solid rgba(212,175,55,0.2);">
    <p style="color:#7e9186;font-size:0.9rem;">
        Made with ❤️ for Quran learners everywhere | 
        <span style="color:#2ecc71;">Keep learning, keep growing</span> 🌱
    </p>
</div>
""", unsafe_allow_html=True)
