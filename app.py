import streamlit as st
import random
import datetime

# ---------------------------
# Predefined Diet Plans
# ---------------------------
diet_plans = {
    "veg": {
        "loss": "Breakfast: Oats + Fruits\nLunch: Dal + Salad\nDinner: Veg Soup + Roti",
        "gain": "Breakfast: Paneer paratha + Milk\nLunch: Rajma + Rice\nDinner: Paneer curry + Roti",
        "maintain": "Breakfast: Poha + Green Tea\nLunch: Veg Pulao + Raita\nDinner: Vegetable curry + Roti"
    },
    "nonveg": {
        "loss": "Breakfast: Boiled eggs + Green Tea\nLunch: Grilled chicken + Salad\nDinner: Fish curry + Veg Soup",
        "gain": "Breakfast: Omelette + Milk\nLunch: Chicken curry + Rice\nDinner: Egg bhurji + Roti",
        "maintain": "Breakfast: Scrambled eggs + Toast\nLunch: Chicken + Brown Rice\nDinner: Fish + Salad"
    }
}

reminders = [
    "💧 Don’t forget to drink water!",
    "🚶 Time for a walk break.",
    "🧘 Do a quick 2 min stretch.",
    "🍎 Eat a fruit instead of junk food."
]

# Simulated step count
def get_step_count():
    return random.randint(2000, 12000)

# Calculate BMI
def calculate_bmi(weight, height):
    height_m = height / 100
    return round(weight / (height_m ** 2), 2)

# Health status based on BMI
def bmi_status(bmi):
    if bmi < 18.5:
        return "Underweight 😟"
    elif 18.5 <= bmi < 24.9:
        return "Normal ✅"
    elif 25 <= bmi < 29.9:
        return "Overweight ⚠️"
    else:
        return "Obese 🚨"

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="Smart Health & Fitness Chatbot", page_icon="🏋️", layout="wide")
st.title("🏋️ Smart Health & Fitness Chatbot")

# Sidebar - User Profile
st.sidebar.header("👤 Your Profile")
name = st.sidebar.text_input("Name", "User")
age = st.sidebar.number_input("Age", 18, 80, 25)
weight = st.sidebar.number_input("Weight (kg)", 30, 200, 70)
height = st.sidebar.number_input("Height (cm)", 100, 220, 170)
goal = st.sidebar.selectbox("Fitness Goal", ["loss", "gain", "maintain"])
diet_pref = st.sidebar.selectbox("Diet Preference", ["veg", "nonveg"])

bmi = calculate_bmi(weight, height)
st.sidebar.write(f"📊 BMI: **{bmi}** → {bmi_status(bmi)}")

# Tabs for Chat and Dashboard
tab1, tab2 = st.tabs(["💬 Chatbot", "📈 Dashboard"])

# ---------------------------
# CHATBOT TAB
# ---------------------------
with tab1:
    st.subheader("🤖 Chat with Fitness Bot")

    if "history" not in st.session_state:
        st.session_state.history = []

    user_input = st.text_input("You:", "")

    if user_input:
        response = "I didn't understand. Try 'diet', 'steps', 'water', 'bmi', 'time'."

        # Rule-based responses
        if "diet" in user_input.lower():
            response = f"Here’s a {diet_pref} diet plan for your goal ({goal}):\n\n{diet_plans[diet_pref][goal]}"
        elif "water" in user_input.lower() or "walk" in user_input.lower():
            response = random.choice(reminders)
        elif "step" in user_input.lower():
            steps = get_step_count()
            calories = round(steps * 0.04, 2)  # approx 0.04 cal per step
            response = f"👣 Steps today: {steps}\n🔥 Calories burned: ~{calories} kcal"
        elif "bmi" in user_input.lower():
            response = f"📊 Your BMI is {bmi} → {bmi_status(bmi)}"
        elif "time" in user_input.lower():
            now = datetime.datetime.now().strftime("%H:%M:%S")
            response = f"⏰ Current time: {now}"

        st.session_state.history.append(("You", user_input))
        st.session_state.history.append(("Bot", response))

    # Show chat history
    for speaker, msg in st.session_state.history:
        if speaker == "You":
            st.markdown(f"**You:** {msg}")
        else:
            st.markdown(f"**🤖 Bot:** {msg}")

# ---------------------------
# DASHBOARD TAB
# ---------------------------
with tab2:
    st.subheader(f"📊 Health Dashboard for {name}")

    steps_today = get_step_count()
    calories_burned = round(steps_today * 0.04, 2)

    col1, col2, col3 = st.columns(3)
    col1.metric("Steps Today", steps_today)
    col2.metric("Calories Burned", f"{calories_burned} kcal")
    col3.metric("Water Intake", "6/8 glasses 💧")

    st.write("👉 Tips for you:")
    st.write(random.choice(reminders))
