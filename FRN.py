import streamlit as st
import datetime
import google.generativeai as genai
import json
import requests

st.set_page_config(page_title="Fasting & Rehab Navigator v3", page_icon="🥗", layout="centered")

# Custom CSS για Dark Mode & High Contrast
st.markdown("""
<style>
    .stApp { background-color: #121212 !important; color: #E0E0E0 !important; }
    .main .block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 500px; }
    .stButton>button {
        width: 100%; height: 3.5rem; font-size: 1.15rem !important;
        font-weight: bold !important; border-radius: 12px !important; margin-bottom: 0.4rem !important;
        background-color: #1F2937 !important; color: #FFFFFF !important; border: 1px solid #374151 !important;
    }
    .stButton>button:hover { background-color: #374151 !important; border-color: #4B5563 !important; }
    .macro-card {
        background-color: #1E1E1E !important; border: 1px solid #333333; padding: 18px;
        border-radius: 14px; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .macro-card h3 { color: #9CA3AF !important; margin-bottom: 5px; }
    .macro-card h2 { color: #60A5FA !important; font-weight: bold; }
    .macro-card h4 { color: #34D399 !important; }
    
    .next-meal-card {
        background-color: #064E3B !important; border-left: 5px solid #10B981 !important;
        color: #ECFDF5 !important; padding: 16px; border-radius: 10px; margin-bottom: 20px;
        font-size: 1.05rem; line-height: 1.5;
    }
    .next-meal-card strong { color: #A7F3D0 !important; }
    
    div[data-baseweb="input"] { background-color: #1F2937 !important; color: #FFFFFF !important; border-color: #374151 !important; }
    input { color: #FFFFFF !important; }
    label { color: #E5E7EB !important; font-weight: 500; }
    .streamlit-expanderHeader { background-color: #1E1E1E !important; color: #E5E7EB !important; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# TIMEZONE & SUPABASE CONFIG
# ---------------------------------------------------------
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

def get_greek_now():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=3)

now_greek = get_greek_now()
date_today = now_greek.strftime("%Y-%m-%d")
current_time_str = now_greek.strftime("%H:%M")

# Header με ενεργοποιημένο το UPSERT (merge-duplicates) για αποφυγή του 409 Conflict
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

# ---------------------------------------------------------
# SUPABASE HELPERS (FETCH & SAVE IN MILLISECONDS)
# ---------------------------------------------------------
def fetch_cloud_data():
    cals, prot, burned, skipped, last_time = 0, 0, 0, 0, None
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            endpoint = f"{SUPABASE_URL}/rest/v1/daily_logs?date=eq.{date_today}&select=*"
            res = requests.get(endpoint, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if data and len(data) > 0:
                    row = data[0]
                    cals = int(row.get("cal_consumed", 0))
                    prot = int(row.get("prot_consumed", 0))
                    burned = int(row.get("workout_burned", 0))
                    skipped = int(row.get("skipped_count", 0))
                    last_time = row.get("last_meal_time", None)
        except Exception:
            pass
    return cals, prot, burned, skipped, last_time

def save_to_cloud():
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            endpoint = f"{SUPABASE_URL}/rest/v1/daily_logs"
            payload = {
                "date": date_today,
                "cal_consumed": int(st.session_state.cal_consumed),
                "prot_consumed": int(st.session_state.protein_consumed),
                "workout_burned": int(st.session_state.workout_burned),
                "skipped_count": int(st.session_state.skipped_count),
                "last_meal_time": str(st.session_state.last_meal_time or "")
            }
            # Χρήση POST με merge-duplicates header για αυτόματο Update
            res = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=5)
            if res.status_code in [200, 201]:
                st.toast("⚡ Ακαριαία Αποθήκευση στο Supabase!", icon="✅")
            else:
                st.error(f"❌ Σφάλμα Supabase HTTP {res.status_code}: {res.text}")
        except Exception as ex:
            st.error(f"❌ Σφάλμα αποθήκευσης: {ex}")

# Initial Load
if 'loaded_from_cloud' not in st.session_state:
    c_i, p_i, b_i, s_i, t_i = fetch_cloud_data()
    st.session_state.cal_consumed = c_i
    st.session_state.protein_consumed = p_i
    st.session_state.workout_burned = b_i
    st.session_state.skipped_count = s_i
    st.session_state.last_meal_time = t_i
    st.session_state.loaded_from_cloud = True

if 'api_key' not in st.session_state: st.session_state.api_key = ""
if 'meal_time_picker' not in st.session_state: st.session_state.meal_time_picker = now_greek.time()
if 'quick_time_picker' not in st.session_state: st.session_state.quick_time_picker = now_greek.time()

base_cal_target = 2350
base_protein_target = 150

st.title("🥗 Fasting & Rehab GPS v3")
st.caption(f"📅 {date_today} | 🕒 Ώρα: {current_time_str} | ⚡ Supabase Powered")

# ---------------------------------------------------------
# DASHBOARD & MACROS
# ---------------------------------------------------------
net_cal_target = base_cal_target + st.session_state.workout_burned
rem_cal = max(0, net_cal_target - st.session_state.cal_consumed)
rem_protein = max(0, base_protein_target - st.session_state.protein_consumed)

st.markdown(f"""
<div class="macro-card">
    <h3>📊 Ημερήσια Πρόοδος</h3>
    <h2>🔥 {st.session_state.cal_consumed} / {net_cal_target} kcal</h2>
    <h4>💪 {st.session_state.protein_consumed}g / {base_protein_target}g Πρωτεΐνη</h4>
</div>
""", unsafe_allow_html=True)

st.progress(min(1.0, st.session_state.protein_consumed / base_protein_target))

# ---------------------------------------------------------
# DYNAMIC RECOMMENDATION
# ---------------------------------------------------------
st.subheader("🎯 Προτεινόμενο Επόμενο Γεύμα")

def get_smart_recommendation():
    if st.session_state.api_key:
        try:
            genai.configure(api_key=st.session_state.api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"User Status: Current Time {current_time_str}, Last Meal Time {st.session_state.last_meal_time or 'None'}, Skipped {st.session_state.skipped_count}, Workout Burned {st.session_state.workout_burned} kcal. Remaining: {rem_cal} kcal, {rem_protein}g protein. Give 2 short Greek sentences for next fasting meal."
            return model.generate_content(prompt).text.strip()
        except Exception:
            pass

    if st.session_state.skipped_count > 0 and rem_protein > 40:
        return f"⚠️ **Λόγω Παράλειψης Γεύματος ({st.session_state.skipped_count}):** Συνιστάται 2 scoops Φυτική Πρωτεΐνη + 2 φέτες Ψωμί με 2 κ.σ. Ταχίνι & 1 Μπανάνα."
    elif rem_protein > 50 and rem_cal > 700:
        return "🥣 **Κύριο Γεύμα:** 2 βαθιά πιάτα Φακές αλάδωτες + 12 Ελιές + 2 φέτες Ψωμί ολικής + 1.5 scoop Φυτική Πρωτεΐνη."
    elif rem_protein > 25:
        return "💪 **Post-Workout / Recovery Snack:** 1.5 scoop Φυτική Πρωτεΐνη + 1 Μπανάνα + 30g Χαλβάς + 30g Κολοκυθόσπορος."
    elif rem_cal > 250:
        return "🥗 **Ελαφρύ Βραδινό:** 3 Φρυγανιές + 10 Ελιές + 30g Κολοκυθόσπορος + Σαλάτα Αγγούρι/Ντομάτα."
    else:
        return "✅ **Οι στόχοι καλύφθηκαν!** 3.5L νερό & εκτέλεση πρωτοκόλλου SP (Elevated Wall Pump)."

st.markdown(f"""<div class="next-meal-card">{get_smart_recommendation()}</div>""", unsafe_allow_html=True)

# ---------------------------------------------------------
# FLEXIBLE MEAL LOGGING
# ---------------------------------------------------------
with st.expander("🍽️ Καταγραφή Γεύματος & Πραγματικής Ώρας", expanded=True):
    col_t1, col_t2 = st.columns([1, 2])
    with col_t1: 
        meal_time = st.time_input("Πραγματική Ώρα Γεύματος", key="meal_time_picker", step=300)
    with col_t2: 
        meal_desc = st.text_input("Τι έφαγες;", placeholder="π.χ. 1 πιάτο φακές, 10 ελιές, 2 φρυγανιές")
    
    api_key_in = st.text_input("Gemini API Key (Προαιρετικό):", value=st.session_state.api_key, type="password")
    if api_key_in: st.session_state.api_key = api_key_in

    if st.button("✨ Καταγραφή Γεύματος"):
        if meal_desc:
            st.session_state.last_meal_time = meal_time.strftime("%H:%M")
            c_add, p_add = 0, 0
            if st.session_state.api_key:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"""Analyze meal: "{meal_desc}". Estimate calories (kcal) & protein (grams). Return ONLY JSON: {{"calories": int, "protein": int}}"""
                    res = model.generate_content(prompt)
                    clean_text = res.text.strip().replace("```json", "").replace("```", "")
                    data = json.loads(clean_text)
                    c_add, p_add = data.get("calories", 0), data.get("protein", 0)
                except Exception:
                    pass
            
            if c_add == 0:
                t_low = meal_desc.lower()
                if "φακε" in t_low: c_add += 300; p_add += 18
                if "ελι" in t_low: c_add += 60; p_add += 1
                if "ψωμ" in t_low or "φρυγανι" in t_low: c_add += 140; p_add += 5
                if "ταχιν" in t_low: c_add += 180; p_add += 5
                if "χαλβα" in t_low: c_add += 160; p_add += 4
                if "πρωτε" in t_low or "scoop" in t_low: c_add += 120; p_add += 25
                if c_add == 0: c_add, p_add = 350, 15

            st.session_state.cal_consumed += c_add
            st.session_state.protein_consumed += p_add
            save_to_cloud()
            st.rerun()

# ---------------------------------------------------------
# WORKOUT LOGGING
# ---------------------------------------------------------
with st.expander("🏃‍♂️ Καταγραφή Προπόνησης k3_rehab"):
    w_cals = st.number_input("Θερμίδες Προπόνησης (kcal)", value=300, step=50)
    if st.button("🔥 Προσθήκη Προπόνησης"):
        st.session_state.workout_burned += w_cals
        save_to_cloud()
        st.rerun()

# ---------------------------------------------------------
# THUMB ACTION BUTTONS
# ---------------------------------------------------------
st.subheader("⚡ Γρήγορες Ενέργειες (Thumb Zone)")
col_a1, col_a2 = st.columns(2)

with col_a1:
    quick_meal_time = st.time_input("Ώρα Γρήγορου Γεύματος", key="quick_time_picker", step=300)
    if st.button("✅ Έφαγα το Προτεινόμενο"):
        st.session_state.cal_consumed += 450
        st.session_state.protein_consumed += 35
        st.session_state.last_meal_time = quick_meal_time.strftime("%H:%M")
        save_to_cloud()
        st.rerun()

    if st.button("🚫 Παράλειψη Γεύματος"):
        st.session_state.skipped_count += 1
        save_to_cloud()
        st.rerun()

with col_a2:
    if st.button("🥤 + 1 Scoop Πρωτεΐνη"):
        st.session_state.cal_consumed += 120
        st.session_state.protein_consumed += 25
        save_to_cloud()
        st.rerun()

    if st.button("🔄 Φόρτωση από Cloud"):
        c_i, p_i, b_i, s_i, t_i = fetch_cloud_data()
        st.session_state.cal_consumed = c_i
        st.session_state.protein_consumed = p_i
        st.session_state.workout_burned = b_i
        st.session_state.skipped_count = s_i
        st.session_state.last_meal_time = t_i
        st.toast("⚡ Ανανεώθηκαν τα δεδομένα από το Supabase!", icon="☁️")
        st.rerun()

st.divider()
if st.button("🔄 Μηδενισμός Ημέρας"):
    st.session_state.cal_consumed = 0
    st.session_state.protein_consumed = 0
    st.session_state.workout_burned = 0
    st.session_state.skipped_count = 0
    st.session_state.last_meal_time = None
    save_to_cloud()
    st.rerun()
