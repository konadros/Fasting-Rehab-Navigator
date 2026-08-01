import streamlit as st
import datetime
import google.generativeai as genai
import json

st.set_page_config(page_title="Fasting & Rehab Navigator", page_icon="🥗", layout="centered")

# Custom CSS για Dark Mode & High Contrast (Thumb Only)
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

# Session State Initialization
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

# Title & Date
today_str = datetime.datetime.now().strftime("%d/%m/%Y")
st.title("🥗 Fasting & Rehab GPS")
st.caption(f"📅 Σήμερα: {today_str} | Powered by Gemini AI 🤖")

# Calculations
net_cal_target = st.session_state.cal_target + st.session_state.workout_burned
rem_cal = max(0, net_cal_target - st.session_state.cal_consumed)
rem_protein = max(0, st.session_state.protein_target - st.session_state.protein_consumed)

# Dashboard
st.markdown(f"""
<div class="macro-card">
    <h3>📊 Ημερήσια Πρόοδος</h3>
    <h2>🔥 {st.session_state.cal_consumed} / {net_cal_target} kcal</h2>
    <h4>💪 {st.session_state.protein_consumed}g / {st.session_state.protein_target}g Πρωτεΐνη</h4>
</div>
""", unsafe_allow_html=True)

st.progress(min(1.0, st.session_state.protein_consumed / st.session_state.protein_target))

# Next Meal Recommendation
st.subheader("🎯 Προτεινόμενο Επόμενο Γεύμα")

if rem_protein > 60 and rem_cal > 800:
    suggestion = "🥣 **Πρωινό / Μεγάλο Γεύμα:** 2 φέτες ψωμί + 2 κ.σ. Ταχίνι + 1.5 scoop Φυτική Πρωτεΐνη + 1 Φρούτο."
elif rem_protein > 30:
    suggestion = "💪 **Post-Workout / Snack:** 1.5 scoop Φυτική Πρωτεΐνη σε νερό + 1 Μπανάνα + 30g Χαλβάς."
elif rem_cal > 300:
    suggestion = "🥗 **Ελαφρύ Βραδινό:** 3 Φρυγανιές + 10 Ελιές + 30g Κολοκυθόσπορος + Σαλάτα Αγγούρι/Ντομάτα."
else:
    suggestion = "✅ **Στόχοι Επιτεύχθηκαν!** Πίεσε νερό (3.5L) & ξεκίνα το πρωτόκολλο SP (Elevated Pump)."

st.markdown(f"""<div class="next-meal-card">{suggestion}</div>""", unsafe_allow_html=True)

# 🧠 GEMINI AI MEAL CALCULATOR EXPANDER
with st.expander("🤖 Έξυπνη Καταγραφή Γεύματος με Gemini AI", expanded=True):
    api_key = st.text_input("Gemini API Key:", type="password", help="Πληκτρολόγησε το API Key σου από το Google AI Studio")
    user_meal_text = st.text_input("Τι έφαγες;", placeholder="π.χ. 1.5 πιάτο φακές, 10 ελιές και 2 φρυγανιές")
    
    if st.button("✨ Υπολογισμός με Gemini"):
        if not api_key:
            st.error("Παρακαλώ καταχώρισε το Gemini API Key σου.")
        elif not user_meal_text:
            st.warning("Γράψε τι έφαγες στο πλαίσιο κειμένου.")
        else:
            try:
                genai.configure(api_key=api_key)
                
                # Χρήση του νέου μοντέλου Gemini 2.5 Flash
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = f"""Analyze this meal: "{user_meal_text}". 
                Estimate total calories (kcal) and total protein (grams). 
                Return ONLY a valid JSON object with format: {{"calories": int, "protein": int}}."""
                
                response = model.generate_content(prompt)
                clean_json = response.text.strip().replace("```json", "").replace("```", "")
                data = json.loads(clean_json)
                
                added_cals = data.get("calories", 0)
                added_prot = data.get("protein", 0)
                
                st.session_state.cal_consumed += added_cals
                st.session_state.protein_consumed += added_prot
                st.success(f"🤖 Gemini: Προστέθηκαν +{added_cals} kcal & +{added_prot}g Πρωτεΐνη!")
                st.rerun()
            except Exception as e:
                # Fallback σε gemini-2.5-pro σε περίπτωση μη διαθεσιμότητας
                try:
                    model = genai.GenerativeModel('gemini-2.5-pro')
                    prompt = f"""Analyze this meal: "{user_meal_text}". 
                    Estimate total calories (kcal) and total protein (grams). 
                    Return ONLY a valid JSON object with format: {{"calories": int, "protein": int}}."""
                    
                    response = model.generate_content(prompt)
                    clean_json = response.text.strip().replace("```json", "").replace("```", "")
                    data = json.loads(clean_json)
                    
                    added_cals = data.get("calories", 0)
                    added_prot = data.get("protein", 0)
                    
                    st.session_state.cal_consumed += added_cals
                    st.session_state.protein_consumed += added_prot
                    st.success(f"🤖 Gemini: Προστέθηκαν +{added_cals} kcal & +{added_prot}g Πρωτεΐνη!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Σφάλμα κατά τον υπολογισμό: {ex}")

# Quick Action Buttons
st.subheader("⚡ Γρήγορες Ενέργειες (Thumb Zone)")
col1, col2 = st.columns(2)
with col1:
    if st.button("✅ Έφαγα το Προτεινόμενο"):
        st.session_state.cal_consumed += 450
        st.session_state.protein_consumed += 35
        st.rerun()
    if st.button("🚫 Παράλειψη Πρωινού"):
        st.toast("Το πρωινό παραλείφθηκε! Αναπροσαρμογή...", icon="⚠️")
        st.rerun()

with col2:
    if st.button("🏃‍♂️ + Προπόνηση (300 kcal)"):
        st.session_state.workout_burned += 300
        st.toast("Προστέθηκαν 300 kcal!", icon="🔥")
        st.rerun()
    if st.button("🥤 + 1 Scoop Πρωτεΐνη"):
        st.session_state.cal_consumed += 120
        st.session_state.protein_consumed += 25
        st.rerun()

st.divider()
if st.button("🔄 Μηδενισμός Ημέρας"):
    st.session_state.cal_consumed = 0
    st.session_state.protein_consumed = 0
    st.session_state.workout_burned = 0
    st.rerun()
