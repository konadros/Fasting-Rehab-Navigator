import streamlit as st
import datetime

st.set_page_config(page_title="Fasting & Rehab Navigator", page_icon="🥗", layout="centered")

# Custom CSS για Dark Mode & Υψηλή Αντίθεση (Thumb Only / High Contrast)
st.markdown("""
<style>
    /* Global Dark Theme Settings */
    .stApp {
        background-color: #121212 !important;
        color: #E0E0E0 !important;
    }
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 500px;
    }
    
    /* Buttons Styling */
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
    
    /* Macro Header Card */
    .macro-card {
        background-color: #1E1E1E !important;
        border: 1px solid #333333;
        padding: 18px;
        border-radius: 14px;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .macro-card h3 {
        color: #9CA3AF !important;
        margin-bottom: 5px;
    }
    .macro-card h2 {
        color: #60A5FA !important;
        font-weight: bold;
    }
    .macro-card h4 {
        color: #34D399 !important;
    }
    
    /* Next Meal Card */
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
    .next-meal-card strong {
        color: #A7F3D0 !important;
    }
    
    /* Input & Expander Dark Fixes */
    div[data-baseweb="input"] {
        background-color: #1F2937 !important;
        color: #FFFFFF !important;
        border-color: #374151 !important;
    }
    input {
        color: #FFFFFF !important;
    }
    label {
        color: #E5E7EB !important;
        font-weight: 500;
    }
    .streamlit-expanderHeader {
        background-color: #1E1E1E !important;
        color: #E5E7EB !important;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Αρχικοποίηση Session State
if 'cal_target' not in st.session_state:
    st.session_state.cal_target = 2350
if 'protein_target' not in st.session_state:
    st.session_state.protein_target = 150
if 'cal_consumed' not in st.session_state:
    st.session_state.cal_consumed = 0
if 'protein_consumed' not in st.session_state:
    st.session_state.protein_consumed = 0
if 'workout_burned' not in st.session_state:
    st.session_state.workout_burned = 0
if 'skipped_meals' not in st.session_state:
    st.session_state.skipped_meals = []

# Τίτλος & Ημερομηνία
today_str = datetime.datetime.now().strftime("%d/%m/%Y")
st.title("🥗 Fasting & Rehab GPS")
st.caption(f"📅 Σήμερα: {today_str} | Στόχος: <85kg & Rehab")

# Δυναμικοί Υπολογισμοί
net_cal_target = st.session_state.cal_target + st.session_state.workout_burned
rem_cal = max(0, net_cal_target - st.session_state.cal_consumed)
rem_protein = max(0, st.session_state.protein_target - st.session_state.protein_consumed)

# Dashboard Πρόοδος
st.markdown(f"""
<div class="macro-card">
    <h3>📊 Ημερήσια Πρόοδος</h3>
    <h2>🔥 {st.session_state.cal_consumed} / {net_cal_target} kcal</h2>
    <h4>💪 {st.session_state.protein_consumed}g / {st.session_state.protein_target}g Πρωτεΐνη</h4>
</div>
""", unsafe_allow_html=True)

st.progress(min(1.0, st.session_state.protein_consumed / st.session_state.protein_target))

# Λογική Προτεινόμενου Επόμενου Γεύματος
st.subheader("🎯 Προτεινόμενο Επόμενο Γεύμα")

if rem_protein > 60 and rem_cal > 800:
    suggestion = "🥣 **Πρωινό / Μεγάλο Γεύμα:** 2 φέτες ψωμί + 2 κ.σ. Ταχίνι + 1.5 scoop Φυτική Πρωτεΐνη + 1 Φρούτο."
elif rem_protein > 30:
    suggestion = "💪 **Post-Workout / Snack:** 1.5 scoop Φυτική Πρωτεΐνη σε νερό + 1 Μπανάνα + 30g Χαλβάς."
elif rem_cal > 300:
    suggestion = "🥗 **Ελαφρύ Βραδινό:** 3 Φρυγανιές + 10 Ελιές + 30g Κολοκυθόσπορος + Σαλάτα Αγγούρι/Ντομάτα."
else:
    suggestion = "✅ **Στόχοι Επιτεύχθηκαν!** Πίεσε νερό (3.5L) & ξεκίνα το πρωτόκολλο SP (Elevated Pump)."

st.markdown(f"""
<div class="next-meal-card">
    {suggestion}
</div>
""", unsafe_allow_html=True)

# THUMB-ONLY ACTION BUTTONS (Περιοχή Αντίχειρα)
st.subheader("⚡ Γρήγορες Ενέργειες (Thumb Zone)")

col1, col2 = st.columns(2)

with col1:
    if st.button("✅ Έφαγα το Προτεινόμενο"):
        st.session_state.cal_consumed += 450
        st.session_state.protein_consumed += 35
        st.rerun()

    if st.button("🚫 Παράλειψη Πρωινού"):
        st.session_state.skipped_meals.append("Breakfast")
        st.toast("Το πρωινό παραλείφθηκε! Αναπροσαρμογή επόμενου γεύματος...", icon="⚠️")
        st.rerun()

with col2:
    if st.button("🏃‍♂️ + Προπόνηση (300 kcal)"):
        st.session_state.workout_burned += 300
        st.toast("Προστέθηκαν 300 kcal από προπόνηση k3_rehab!", icon="🔥")
        st.rerun()

    if st.button("🥤 + 1 Scoop Πρωτεΐνη"):
        st.session_state.cal_consumed += 120
        st.session_state.protein_consumed += 25
        st.rerun()

st.divider()

# Προσαρμοσμένη Καταγραφή
with st.expander("📝 Καταγραφή Άλλου Γεύματος / Μηδενισμός"):
    custom_cals = st.number_input("Θερμίδες (kcal)", value=300, step=50)
    custom_prot = st.number_input("Πρωτεΐνη (g)", value=20, step=5)
    if st.button("Προσθήκη Γεύματος"):
        st.session_state.cal_consumed += custom_cals
        st.session_state.protein_consumed += custom_prot
        st.rerun()
    
    if st.button("🔄 Μηδενισμός Ημέρας"):
        st.session_state.cal_consumed = 0
        st.session_state.protein_consumed = 0
        st.session_state.workout_burned = 0
        st.rerun()
