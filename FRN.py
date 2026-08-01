import streamlit as st
import datetime
import google.generativeai as genai
import json

st.set_page_config(page_title="Fasting & Rehab Navigator", page_icon="🥗", layout="centered")

# Custom CSS για Dark Mode & High Contrast (Thumb-Only / Mobile First)
st.markdown("""
<style>
    .stApp {
        background-color: #121212 !important;
        color: #E0E0E0 !important;
    }
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 500px;
    }
    .stButton>button {
        width: 100%;
        height: 3.5rem;
        font-size: 1.15rem !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        margin-bottom: 0.4rem !important;
        background-color: #1F2937 !important;
        color: #FFFFFF !important;
        border: 1px solid #374151 !important;
    }
    .stButton>button:hover {
        background-color: #374151 !important;
        border-color: #4B5563 !important;
    }
    .macro-card {
        background-color: #1E1E1E !important;
        border: 1px solid #333333;
        padding: 18px;
        border-radius: 14px;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .macro-card h3 { color: #9CA3AF !important; margin-bottom: 5px; }
    .macro-card h2 { color: #60A5FA !important; font-weight: bold; }
    .macro-card h4 { color: #34D399 !important; }
    
    .next-meal-card {
        background-color: #064E3B !important;
        border-left: 5px solid #10B981 !important;
        color: #ECFDF5 !important;
        padding: 16px;
        border-radius: 10px;
        margin-bottom: 20px;
        font-size: 1.05rem;
        line-height: 1.5;
    }
    .next-meal-card strong { color: #A7F3D0 !important; }
    
    .recovery-banner {
        background-color: #312E81 !important;
        border-left: 5px solid #6366F1 !important;
        color: #EEF2FF !important;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 15px;
        font-size: 0.95rem;
    }
    
    div[data-baseweb="input"] {
        background-color: #1F2937 !important;
        color: #FFFFFF !important;
        border-color: #374151 !important;
    }
    input { color: #FFFFFF !important; }
    label { color: #E5E7EB !important; font-weight: 500; }
    .streamlit-expanderHeader {
        background-color: #1E1E1E !important;
        color: #E5E7EB !important;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. SESSION STATE & HISTORICAL RECOVERY TRACKING
# ---------------------------------------------------------
if 'history' not in st.session_state:
    st.session_state.history = {}

if 'date_today' not in st.session_state:
    st.session_state.date_today = datetime.date.today().strftime("%Y-%m-%d")

# Carry-over / Recovery adjustment from previous day
prev_date = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
prev_day_data = st.session_state.history.get(prev_date, {})

prev_workout_load = prev_day_data.get('workout_load', 'Normal')

# Base Targets
base_cal_target = 2350
base_protein_target = 150

# Adjust target based on previous day's heavy load
if prev_workout_load in ['Υψηλό (Tabata T1/T2 / Run)', 'Heavy']:
    base_cal_target += 150
    base_protein_target += 15

if 'cal_target' not in st.session_state:
    st.session_state.cal_target = base_cal_target
if 'protein_target' not in st.session_state:
    st.session_state.protein_target = base_protein_target
if 'cal_consumed' not in st.session_state:
    st.session_state.cal_consumed = 0
if 'protein_consumed' not in st.session_state:
    st.session_state.protein_consumed = 0
if 'workout_burned' not in st.session_state:
    st.session_state.workout_burned = 0
if 'workout_load' not in st.session_state:
    st.session_state.workout_load = 'Κανονικό'
if 'skipped_count' not in st.session_state:
    st.session_state.skipped_count = 0
if 'last_meal_time' not in st.session_state:
    st.session_state.last_meal_time = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

# Header
st.title("🥗 Fasting & Rehab GPS")
st.caption(f"📅 Σήμερα: {st.session_state.date_today} | 🎯 Στόχος: <85kg & k3_rehab")

# Display Carry-over Recovery Banner if active
if prev_day_data:
    st.markdown(f"""
    <div class="recovery-banner">
        🔄 <b>Αποκατάσταση από Χθες:</b> Φορτίο: {prev_workout_load} | Προσαρμογή Στόχων: +{base_cal_target - 2350} kcal, +{base_protein_target - 150}g Πρωτεΐνη.
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. DASHBOARD & MACROS
# ---------------------------------------------------------
net_cal_target = st.session_state.cal_target + st.session_state.workout_burned
rem_cal = max(0, net_cal_target - st.session_state.cal_consumed)
rem_protein = max(0, st.session_state.protein_target - st.session_state.protein_consumed)

st.markdown(f"""
<div class="macro-card">
    <h3>📊 Ημερήσια Πρόοδος</h3>
    <h2>🔥 {st.session_state.cal_consumed} / {net_cal_target} kcal</h2>
    <h4>💪 {st.session_state.protein_consumed}g / {st.session_state.protein_target}g Πρωτεΐνη</h4>
</div>
""", unsafe_allow_html=True)

st.progress(min(1.0, st.session_state.protein_consumed / st.session_state.protein_target))

# ---------------------------------------------------------
# 3. DYNAMIC NEXT MEAL SUGGESTION (TIMED & AI-POWERED)
# ---------------------------------------------------------
st.subheader("🎯 Προτεινόμενο Επόμενο Γεύμα")

current_time_str = datetime.datetime.now().strftime("%H:%M")

def get_smart_recommendation():
    if st.session_state.api_key:
        try:
            genai.configure(api_key=st.session_state.api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""
            User Profile: 180cm, 87kg (Target <85kg), Orthodox Fasting (Lentils, Tahini, Halva, Olives, Bread, Plant Protein).
            Current Status:
            - Current Time: {current_time_str}
            - Last Meal Time: {st.session_state.last_meal_time or 'None'}
            - Skipped Meals Count Today: {st.session_state.skipped_count}
            - Workout Burned Today: {st.session_state.workout_burned} kcal (Load: {st.session_state.workout_load})
            - Remaining Calories Needed: {rem_cal} kcal
            - Remaining Protein Needed: {rem_protein} g
            Provide a short, direct, actionable meal suggestion in Greek (2-3 sentences max).
            """
            res = model.generate_content(prompt)
            return res.text.strip()
        except Exception:
            pass

    # Standard Rule-based Fallback Recommendation
    if st.session_state.skipped_count > 0 and rem_protein > 40:
        return f"⚠️ **Λόγω Παράλειψης Γεύματος ({st.session_state.skipped_count}):** Συνιστάται συμπυκνωμένο γεύμα υψηλής πρωτεΐνης: 2 scoops Φυτική Πρωτεΐνη σε νερό + 2 φέτες Ψωμί με 2 κ.σ. Ταχίνι & 1 Μπανάνα."
    elif rem_protein > 50 and rem_cal > 700:
        return "🥣 **Κύριο Γεύμα:** 2 βαθιά πιάτα Φακές αλάδωτες + 12 Ελιές + 2 φέτες Ψωμί ολικής + 1.5 scoop Φυτική Πρωτεΐνη."
    elif rem_protein > 25:
        return "💪 **Post-Workout / Recovery Snack:** 1.5 scoop Φυτική Πρωτεΐνη + 1 Μπανάνα + 30g Χαλβάς + 30g Κολοκυθόσπορος."
    elif rem_cal > 250:
        return "🥗 **Ελαφρύ Βραδινό:** 3 Φρυγανιές + 10 Ελιές + 30g Κολοκυθόσπορος + Σαλάτα Αγγούρι/Ντομάτα."
    else:
        return "✅ **Οι στόχοι καλύφθηκαν!** 3.5L νερό & εκτέλεση πρωτοκόλλου SP (Elevated Wall Pump)."

suggestion_text = get_smart_recommendation()

st.markdown(f"""<div class="next-meal-card">{suggestion_text}</div>""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. FLEXIBLE MEAL LOGGING (TIME + TEXT / GEMINI)
# ---------------------------------------------------------
with st.expander("🍽️ Καταγραφή Γεύματος & Ώρας", expanded=True):
    col_t1, col_t2 = st.columns([1, 2])
    with col_t1:
        meal_time = st.time_input("Ώρα Γεύματος", datetime.datetime.now().time())
    with col_t2:
        meal_desc = st.text_input("Τι έφαγες;", placeholder="π.χ. 1 πιάτο φακές, 10 ελιές, 2 φρυγανιές")
    
    api_key_in = st.text_input("Gemini API Key (Προαιρετικό):", value=st.session_state.api_key, type="password")
    if api_key_in:
        st.session_state.api_key = api_key_in

    if st.button("✨ Καταγραφή Γεύματος"):
        if not meal_desc:
            st.warning("Παρακαλώ συμπλήρωσε τι έφαγες.")
        else:
            st.session_state.last_meal_time = meal_time.strftime("%H:%M")
            success = False
            
            if st.session_state.api_key:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"""Analyze meal: "{meal_desc}". Estimate calories (kcal) & protein (grams). Return ONLY JSON: {{"calories": int, "protein": int}}"""
                    res = model.generate_content(prompt)
                    clean_j = res.text.strip().replace("```json", "").replace("```", "")
                    data = json.loads(clean_j)
                    c_add, p_add = data.get("calories", 0), data.get("protein", 0)
                    st.session_state.cal_consumed += c_add
                    st.session_state.protein_consumed += p_add
                    st.success(f"🤖 Gemini ({st.session_state.last_meal_time}): +{c_add} kcal | +{p_add}g Πρωτεΐνη")
                    success = True
                    st.rerun()
                except Exception:
                    st.warning("API limit/error: Μετάβαση σε τοπικό υπολογισμό...")
            
            if not success:
                t_low = meal_desc.lower()
                c_add, p_add = 0, 0
                if "φακε" in t_low or "φακές" in t_low: c_add += 300; p_add += 18
                if "ελι" in t_low: c_add += 60; p_add += 1
                if "ψωμ" in t_low or "φρυγανι" in t_low: c_add += 140; p_add += 5
                if "ταχιν" in t_low: c_add += 180; p_add += 5
                if "χαλβα" in t_low: c_add += 160; p_add += 4
                if "πρωτε" in t_low or "scoop" in t_low: c_add += 120; p_add += 25
                if "μπαναν" in t_low or "φρουτ" in t_low: c_add += 90; p_add += 1
                if c_add == 0: c_add, p_add = 350, 15
                
                st.session_state.cal_consumed += c_add
                st.session_state.protein_consumed += p_add
                st.success(f"🧮 Τοπικός Υπολογισμός ({st.session_state.last_meal_time}): +{c_add} kcal | +{p_add}g Πρωτεΐνη")
                st.rerun()

# ---------------------------------------------------------
# 5. FLEXIBLE WORKOUT LOGGING (k3_rehab Load & Duration)
# ---------------------------------------------------------
with st.expander("🏃‍♂️ Καταγραφή Προπόνησης k3_rehab"):
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        w_time = st.time_input("Ώρα Προπόνησης", datetime.datetime.now().time())
        w_duration = st.number_input("Διάρκεια (λεπτά)", value=45, step=5)
    with col_w2:
        w_load = st.selectbox("Ένταση / Φορτίο", ["Ήπιο (SP / Walk)", "Κανονικό (A/B)", "Υψηλό (Tabata T1/T2 / Run)"])
        w_cals = st.number_input("Θερμίδες (kcal)", value=300, step=50)
    
    if st.button("🔥 Προσθήκη Προπόνησης"):
        st.session_state.workout_burned += w_cals
        st.session_state.workout_load = w_load
        st.toast(f"Προπόνηση καταγράφηκε! (+{w_cals} kcal, Φορτίο: {w_load})", icon="💪")
        st.rerun()

# ---------------------------------------------------------
# 6. THUMB-ONLY ACTION BUTTONS
# ---------------------------------------------------------
st.subheader("⚡ Γρήγορες Ενέργειες (Thumb Zone)")
col_a1, col_a2 = st.columns(2)

with col_a1:
    if st.button("✅ Έφαγα το Προτεινόμενο"):
        st.session_state.cal_consumed += 450
        st.session_state.protein_consumed += 35
        st.session_state.last_meal_time = datetime.datetime.now().strftime("%H:%M")
        st.rerun()

    if st.button("🚫 Παράλειψη Γεύματος"):
        st.session_state.skipped_count += 1
        st.toast(f"Παραλείφθηκε γεύμα! (Σύνολο: {st.session_state.skipped_count}). Αναπροσαρμογή επόμενου...", icon="⚠️")
        st.rerun()

with col_a2:
    if st.button("🥤 + 1 Scoop Πρωτεΐνη"):
        st.session_state.cal_consumed += 120
        st.session_state.protein_consumed += 25
        st.rerun()

    if st.button("🌙 Κλείσιμο Ημέρας (Save)"):
        cal_def = net_cal_target - st.session_state.cal_consumed
        prot_short = st.session_state.protein_target - st.session_state.protein_consumed
        
        st.session_state.history[st.session_state.date_today] = {
            'cal_deficit': cal_def,
            'protein_shortfall': prot_short,
            'workout_load': st.session_state.workout_load
        }
        st.success("Η ημέρα αποθηκεύτηκε! Οι ανάγκες αποκατάστασης θα μεταφερθούν αύριο.")

st.divider()
if st.button("🔄 Μηδενισμός Ημέρας"):
    st.session_state.cal_consumed = 0
    st.session_state.protein_consumed = 0
    st.session_state.workout_burned = 0
    st.session_state.skipped_count = 0
    st.rerun()
