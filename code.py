import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="MoneyFlow", page_icon="💰", layout="wide")

# ====================================================
# USER AUTHENTICATION (LOGIN & SIGN UP)
# ====================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Temporary database to hold users while the app is running
if 'user_database' not in st.session_state:
    st.session_state.user_database = {
        "shaheer": {"name": "Shaheer", "password": "password123"},
        "amna": {"name": "Amna", "password": "student2026"}
    }

if not st.session_state.logged_in:
    st.title("Welcome to MoneyFlow 🔒")
    st.write("Please log in or create an account to access your financial dashboard.")
    
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])
    
    # --- LOG IN TAB ---
    with tab1:
        with st.form("login_form"):
            login_username = st.text_input("Username").lower().strip()
            login_password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Log In", type="primary")

            if submit_login:
                db = st.session_state.user_database
                if login_username in db and db[login_username]["password"] == login_password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = login_username
                    st.session_state.current_name = db[login_username]["name"]
                    st.rerun()
                else:
                    st.error("⚠️ Incorrect username or password.")
                    
    # --- SIGN UP TAB ---
    with tab2:
        with st.form("signup_form"):
            new_name = st.text_input("Full Name (e.g., John Doe)")
            new_username = st.text_input("Choose a Username").lower().strip()
            new_password = st.text_input("Choose a Password", type="password")
            submit_signup = st.form_submit_button("Create Account", type="primary")
            
            if submit_signup:
                if new_username in st.session_state.user_database:
                    st.error("⚠️ That username is already taken. Please choose another.")
                elif new_username == "" or new_password == "" or new_name == "":
                    st.warning("⚠️ Please fill out all fields.")
                else:
                    st.session_state.user_database[new_username] = {
                        "name": new_name, 
                        "password": new_password
                    }
                    st.success(f"✅ Account created for {new_name}! You can now Log In on the other tab.")

    st.stop() # Stops the dashboard from showing until logged in

# ====================================================
# MAIN APP HEADER & LOGOUT / ROLLOVER
# ====================================================
col1, col2, col3 = st.columns([6, 2, 3])
with col1:
    st.write(f"### Welcome back, {st.session_state.current_name}! 👋")
    
with col2:
    if st.button("Normal Log Out", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
        
with col3:
    # THE NEW ROLLOVER FEATURE
    if st.button("End Month & Save Leftovers", type="primary", use_container_width=True):
        # 1. Calculate exactly what is left
        current_salary = st.session_state.get('salary_input', 0.0)
        current_expenses = st.session_state.expense_df['Price (PKR)'].sum() if not st.session_state.expense_df.empty else 0
        locked_needs = st.session_state.recurring_needs_df['Cost (PKR)'].sum() if not st.session_state.recurring_needs_df.empty else 0
        allocated_goals = st.session_state.goals_df['Saved (PKR)'].sum() if not st.session_state.goals_df.empty else 0
        
        unallocated = current_salary - locked_needs - current_expenses - allocated_goals
        
        # 2. Sweep unallocated money into a Rollover Savings goal
        if unallocated > 0:
            if 'Rollover Savings' not in st.session_state.goals_df['Goal Name'].values:
                new_goal = pd.DataFrame([{'Goal Name': 'Rollover Savings', 'Target (PKR)': 0.0, 'Saved (PKR)': unallocated, 'Type': 'Dream Jar (Savings)'}])
                st.session_state.goals_df = pd.concat([st.session_state.goals_df, new_goal], ignore_index=True)
            else:
                idx = st.session_state.goals_df.index[st.session_state.goals_df['Goal Name'] == 'Rollover Savings'].tolist()[0]
                st.session_state.goals_df.at[idx, 'Saved (PKR)'] += unallocated
                
        # 3. Wipe the daily expenses clean for the new month
        st.session_state.expense_df = pd.DataFrame(columns=['Item Name', 'Price (PKR)', 'Category', 'Type'])
        
        # 4. Log out
        st.session_state.logged_in = False
        st.rerun()

st.markdown("---")

# ====================================================
# INITIAL SETUP & STATE MANAGEMENT
# ====================================================
if 'expense_df' not in st.session_state:
    st.session_state.expense_df = pd.DataFrame(columns=['Item Name', 'Price (PKR)', 'Category', 'Type'])

if 'available_categories' not in st.session_state:
    st.session_state.available_categories = ['Food', 'Transport', 'Gaming', 'Books', 'Bills', 'Rent', 'Car Maintenance']

if 'recurring_needs_df' not in st.session_state:
    st.session_state.recurring_needs_df = pd.DataFrame(columns=['Need Name', 'Cost (PKR)'])

if 'goals_df' not in st.session_state:
    st.session_state.goals_df = pd.DataFrame(columns=['Goal Name', 'Target (PKR)', 'Saved (PKR)', 'Type'])

if 'suggestions_list' not in st.session_state:
    st.session_state.suggestions_list = []

st.title("Student Spending App Prototype 💰")

# ====================================================
# PART 1: INCOME & SMART EXPENSE LOGGING
# ====================================================
st.header("Part 1: Income & Expense Logging")

# CRITICAL UPDATE: The key="salary_input" here lets the rollover button read the salary!
total_salary = st.number_input('Enter Monthly Salary / Pocket Money (PKR):', min_value=0.0, value=0.0, step=1000.0, key="salary_input")
total_expenses = st.session_state.expense_df['Price (PKR)'].sum()
potential_savings = total_salary - total_expenses

if total_salary < 0:
    st.error("⚠️ Error: Salary cannot be negative! Please enter a valid positive number.")
else:
    if potential_savings >= 0:
        st.success(f"Available Balance: {potential_savings:,.2f} PKR")
    else:
        st.error(f"Available Balance: {potential_savings:,.2f} PKR (Over Budget!)")

st.markdown("---")

st.subheader("Log New Expense")
with st.form("log_expense_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        item_name = st.text_input("Item Name (e.g., Latte, Electricity Bill):")
        price = st.number_input("Price (PKR):", min_value=0.0, step=100.0)
    with col2:
        category_dropdown = st.selectbox("Category:", st.session_state.available_categories)
        type_toggle = st.radio("Type:", ['Need', 'Want'], horizontal=True)
        
    if st.form_submit_button("Log Expense"):
        if item_name.strip() != "" and price > 0:
            new_row = pd.DataFrame([{
                'Item Name': item_name,
                'Price (PKR)': price,
                'Category': category_dropdown,
                'Type': type_toggle
            }])
            st.session_state.expense_df = pd.concat([st.session_state.expense_df, new_row], ignore_index=True)
            st.rerun()

with st.expander("Add Custom Category"):
    new_cat = st.text_input("New Category Name:")
    if st.button("Add Category") and new_cat and new_cat not in st.session_state.available_categories:
        st.session_state.available_categories.append(new_cat)
        st.rerun()

st.markdown("---")
st.subheader("Dynamic Entry Table")

if st.session_state.expense_df.empty:
    st.info("No expenses logged yet.")
else:
    st.dataframe(st.session_state.expense_df, use_container_width=True)
    if st.button("Clear All Logs", type="primary"):
        st.session_state.expense_df = pd.DataFrame(columns=['Item Name', 'Price (PKR)', 'Category', 'Type'])
        st.rerun()

metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("Total Salary", f"{total_salary:,.2f} PKR")
metric_col2.metric("Total Expenses", f"{total_expenses:,.2f} PKR")
metric_col3.metric("Potential Savings", f"{potential_savings:,.2f} PKR")

# ====================================================
# PART 2: VISUAL ANALYTICS DASHBOARD
# ====================================================
st.markdown("---")
st.header("Part 2: Visual Analytics Dashboard")

expense_df = st.session_state.expense_df
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    if not expense_df.empty:
        needs_total = expense_df[expense_df['Type'] == 'Need']['Price (PKR)'].sum()
        wants_total = expense_df[expense_df['Type'] == 'Want']['Price (PKR)'].sum()
    else:
        needs_total, wants_total = 0, 0
        
    savings_total = total_salary - (needs_total + wants_total)
    if savings_total < 0: savings_total = 0
        
    labels_behavior = ['Needs', 'Wants', 'Savings']
    values_behavior = [needs_total, wants_total, savings_total]
    colors_behavior = ['#636EFA', '#FFA15A', '#00CC96']
    
    alert_text = "✅ On track (50/30/20 Rule)"
    if total_salary > 0 and wants_total > (total_salary * 0.30):
        colors_behavior[1] = '#FF3333'
        alert_text = "⚠️ ALERT: Wants exceed 30% of Salary!"
        
    fig_behavior = go.Figure(data=[go.Pie(labels=labels_behavior, values=values_behavior, marker=dict(colors=colors_behavior), hole=0.4)])
    fig_behavior.update_layout(title_text=f"Behavioral Split<br><sup>{alert_text}</sup>", margin=dict(t=50, b=0, l=0, r=0))
    st.plotly_chart(fig_behavior, use_container_width=True)

with chart_col2:
    if not expense_df.empty:
        cat_totals = expense_df.groupby('Category')['Price (PKR)'].sum().reset_index()
        fig_category = go.Figure(data=[go.Pie(labels=cat_totals['Category'], values=cat_totals['Price (PKR)'])])
    else:
        fig_category = go.Figure(data=[go.Pie(labels=['No Data Yet'], values=[1], marker=dict(colors=['#e0e0e0']))])

    fig_category.update_layout(title_text="Spending by Category", margin=dict(t=50, b=0, l=0, r=0))
    st.plotly_chart(fig_category, use_container_width=True)

# ====================================================
# PART 3: SMART GOAL SETTING
# ====================================================
st.markdown("---")
st.header("Part 3: Smart Goal Setting")

st.subheader("1. Needs Prioritization (Lock Your Salary)")
with st.form("add_need_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        need_name = st.text_input("Locked Need (e.g., Tuition, Rent):")
    with col2:
        need_cost = st.number_input("Cost (PKR):", min_value=0.0, step=500.0)
        
    if st.form_submit_button("Lock Need") and need_name.strip() != "" and need_cost > 0:
        new_need = pd.DataFrame([{'Need Name': need_name, 'Cost (PKR)': need_cost}])
        st.session_state.recurring_needs_df = pd.concat([st.session_state.recurring_needs_df, new_need], ignore_index=True)
        st.rerun()

total_locked = st.session_state.recurring_needs_df['Cost (PKR)'].sum() if not st.session_state.recurring_needs_df.empty else 0
adjusted_salary = total_salary - total_locked

st.write(f"**Total Salary:** {total_salary:,.2f} PKR")
st.write(f"🔒 **Locked for Recurring Needs:** -{total_locked:,.2f} PKR")
st.markdown(f"<h3 style='color: #d32f2f;'>Safe-to-Spend Balance: {adjusted_salary:,.2f} PKR</h3>", unsafe_allow_html=True)

if not st.session_state.recurring_needs_df.empty:
    st.dataframe(st.session_state.recurring_needs_df, use_container_width=True)

st.markdown("---")
st.subheader("2. The Dream Jar & Luxury Wishlist")
with st.form("add_goal_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 1, 1.5])
    with col1:
        goal_name = st.text_input("Goal Name (e.g., Exam Fees):")
    with col2:
        goal_target = st.number_input("Target (PKR):", min_value=0.0, step=1000.0)
    with col3:
        goal_type = st.selectbox("Type:", ['Dream Jar (Savings)', 'Luxury Wishlist (Want)'])
        
    if st.form_submit_button("Add Goal") and goal_name.strip() != "" and goal_target > 0:
        new_goal = pd.DataFrame([{'Goal Name': goal_name, 'Target (PKR)': goal_target, 'Saved (PKR)': 0.0, 'Type': goal_type}])
        st.session_state.goals_df = pd.concat([st.session_state.goals_df, new_goal], ignore_index=True)
        st.rerun()

total_allocated = st.session_state.goals_df['Saved (PKR)'].sum() if not st.session_state.goals_df.empty else 0
unallocated_savings = adjusted_salary - total_expenses - total_allocated

st.markdown(f"<h3 style='color: #2e7d32;'>Unallocated Savings Available: {unallocated_savings:,.2f} PKR</h3>", unsafe_allow_html=True)

if st.session_state.goals_df.empty:
    st.info("No goals set yet. Add one above!")
else:
    st.write("**Fund Your Goals:**")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        allocate_dropdown = st.selectbox("Select Goal:", st.session_state.goals_df['Goal Name'].tolist())
    with col2:
        allocate_amount = st.number_input("Amount (PKR):", min_value=0.0, step=500.0, key="alloc_amount")
    with col3:
        st.write("") 
        st.write("")
        allocate_btn = st.button("Fund Goal", type="primary")

    if allocate_btn and allocate_dropdown and allocate_amount > 0:
        if allocate_amount > unallocated_savings:
            st.error(f"⚠️ Error: You only have {unallocated_savings:,.2f} PKR available. You cannot allocate {allocate_amount:,.2f} PKR.")
        else:
            idx = st.session_state.goals_df.index[st.session_state.goals_df['Goal Name'] == allocate_dropdown].tolist()[0]
            target = st.session_state.goals_df.at[idx, 'Target (PKR)']
            current_saved = st.session_state.goals_df.at[idx, 'Saved (PKR)']
            
            if current_saved + allocate_amount > target:
                allocate_amount = target - current_saved
                st.warning(f"⚠️ Amount reduced to {allocate_amount:,.2f} PKR to exactly meet target!")
            
            st.session_state.goals_df.at[idx, 'Saved (PKR)'] += allocate_amount
            st.rerun()

    st.markdown("---")
    for index, row in st.session_state.goals_df.iterrows():
        name, target, saved, g_type = row['Goal Name'], row['Target (PKR)'], row['Saved (PKR)'], row['Type']
        pct_float = saved / target if target > 0 else 0
        if pct_float > 1.0: pct_float = 1.0 
        
        st.write(f"**{name}** ({g_type})")
        st.progress(pct_float)
        
        status_text = f"{saved:,.2f} / {target:,.2f} PKR ({pct_float * 100:.1f}%)"
        luxury_text = ""
        if 'Luxury' in g_type and saved < target and total_salary > 0:
            daily_income = total_salary / 30
            days_required = (target - saved) / daily_income
            luxury_text = f" | *Requires {days_required:.1f} days of zero-spending to afford.*"
            
        st.caption(f"{status_text} {luxury_text}")
        st.write("")

# ====================================================
# PART 4: SMART RECOMMENDATIONS & ALTERNATIVES
# ====================================================
st.markdown("---")
st.header("Part 4: Smart Recommendations & Alternatives")

alternatives_db = {
    'netflix': '📺 Switch to Tubi, YouTube Free Movies, or the Hulu/Disney Student Bundle.',
    'spotify': '🎵 Use the ad-supported free tier, local radio apps, or get 50% off with a Student Plan.',
    'microsoft office': '💻 Switch to Google Docs, LibreOffice, or get it FREE with your NUST student email.',
    'gym': '🏋️ Use campus facilities or free YouTube calisthenics routines.',
    'adobe': '🎨 Switch to Canva, Photopea, or DaVinci Resolve (for video).'
}
student_discount_brands = ['apple', 'samsung', 'levis', 'nike', 'adidas', 'spotify', 'mcdonalds']

st.subheader("1. Subscription Auditor & Discount Finder")
if st.button("Scan My Spending", type="primary"):
    if expense_df.empty:
        st.warning("No expenses logged yet. Log some 'Wants' in Part 1 to get recommendations!")
    else:
        wants_df = expense_df[expense_df['Type'] == 'Want']
        if wants_df.empty:
            st.success("Great job! You haven't logged any 'Wants' yet.")
        else:
            st.write("--- 🔍 **SMART AUDIT RESULTS** ---")
            found_recommendation = False
            for index, row in wants_df.iterrows():
                item_name = str(row['Item Name']).lower()
                for key, alternative in alternatives_db.items():
                    if key in item_name:
                        st.info(f"**💡 Alternative found for '{row['Item Name']}':**\n\n {alternative}")
                        found_recommendation = True
                for brand in student_discount_brands:
                    if brand in item_name:
                        st.warning(f"**🎓 Discount Alert for '{row['Item Name']}':**\n\n {brand.title()} usually offers a Student Discount! Make sure you show your university ID.")
                        found_recommendation = True
            if not found_recommendation:
                st.success("No specific matches found, but always ask if a student discount is available at checkout!")

st.markdown("---")
st.subheader("2. The 'Price-Per-Use' Logic Test")
with st.form("ppu_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        ppu_item = st.text_input("Item:", value="Football Boots")
    with col2:
        ppu_price = st.number_input("Price (PKR):", min_value=0.0, value=20000.0, step=1000.0)
    with col3:
        ppu_uses = st.number_input("Est. Uses/Year:", min_value=1, value=50, step=1)
        
    if st.form_submit_button("Calculate Value"):
        cost_per_use = ppu_price / ppu_uses
        if cost_per_use > 500: rating = "<span style='color: #d32f2f;'><b>High Cost!</b> Think carefully before buying.</span>"
        elif cost_per_use > 100: rating = "<span style='color: #ff9800;'><b>Moderate.</b> Make sure you really want it.</span>"
        else: rating = "<span style='color: #2e7d32;'><b>Great Value!</b> A solid investment for how much you'll use it.</span>"
            
        st.markdown(f"#### Cost per use: {cost_per_use:,.2f} PKR")
        st.markdown(rating, unsafe_allow_html=True)

# ====================================================
# PART 5: FINAL FEEDBACK & SUGGESTION BOX
# ====================================================
st.markdown("---")
st.header("Part 5: Final Feedback & Suggestion Box")
st.write("Help us improve! What new categories, tools, or features would you like to see next?")

with st.form("feedback_form", clear_on_submit=True):
    suggestion_text = st.text_area("Idea:", placeholder='e.g., "Add a currency converter" or "Add a shared budget for roommates"', height=100)
    if st.form_submit_button("Submit Request", type="primary") and suggestion_text.strip() != "":
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        st.session_state.suggestions_list.append({'time': timestamp, 'text': suggestion_text.strip()})
        st.rerun()

st.markdown("---")
if not st.session_state.suggestions_list:
    st.caption("*No feedback submitted yet. Be the first!*")
else:
    st.success("✅ Thank you! Your feedback has been recorded:")
    for item in reversed(st.session_state.suggestions_list):
        st.markdown(f"""
        <div style='padding: 10px; border-left: 4px solid #2196F3; margin-bottom: 10px; background-color: #f1f8ff; border-radius: 5px;'>
            <small style='color: gray;'>{item['time']}</small><br>
            <span style='color: #333;'><b>{item['text']}</b></span>
        </div>
        """, unsafe_allow_html=True)
