import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import database as db
import utils

st.set_page_config(page_title="Smart Finance Analyzer", page_icon="📊", layout="wide")
db.init_db()

# Initialize session state for login
if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.username = None

CATEGORIES = [
    "Food & Dining", "Transportation", "Utilities & Bills",
    "Entertainment", "Shopping", "Healthcare", "Education", "Salary/Allowance", "Other"
]

# --- AUTHENTICATION VIEW ---
def auth_page():
    st.title("Smart Personal Finance & Budget Analyzer")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                user = db.get_user(username)
                if user and utils.verify_password(password, user[2]):
                    st.session_state.user_id = user[0]
                    st.session_state.username = user[1]
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    with tab2:
        with st.form("signup_form"):
            new_user = st.text_input("Choose a Username")
            new_pass = st.text_input("Choose a Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Create Account")
            if submitted:
                if not new_user or not new_pass:
                    st.warning("Please fill in all fields.")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match.")
                else:
                    hashed = utils.hash_password(new_pass)
                    if db.create_user(new_user, hashed):
                        st.success("Account created! Switch to the Login tab.")
                    else:
                        st.error("Username already exists.")

# --- MAIN DASHBOARD VIEW ---
def main_dashboard():
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.username = None
        st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Set Monthly Category Budget")
    with st.sidebar.form("budget_form"):
        b_cat = st.selectbox("Category", [c for c in CATEGORIES if c != "Salary/Allowance"])
        b_limit = st.number_input("Monthly Limit (₹)", min_value=100.0, step=500.0)
        if st.form_submit_button("Save Budget"):
            db.set_budget(st.session_state.user_id, b_cat, b_limit)
            st.sidebar.success(f"Budget updated for {b_cat}")

    st.title("Financial Overview & Analytics")

    # Fetch user data
    df = db.get_transactions(st.session_state.user_id)
    budgets_df = db.get_budgets(st.session_state.user_id)

    # Top KPI Metrics
    total_income = df[df["type"] == "Income"]["amount"].sum() if not df.empty else 0.0
    total_expense = df[df["type"] == "Expense"]["amount"].sum() if not df.empty else 0.0
    net_balance = total_income - total_expense
    savings_rate = ((total_income - total_expense) / total_income * 100) if total_income > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Income", f"₹{total_income:,.2f}")
    col2.metric("Total Expenses", f"₹{total_expense:,.2f}")
    col3.metric("Net Balance", f"₹{net_balance:,.2f}")
    col4.metric("Savings Rate", f"{savings_rate:.1f}%")

    # Budget Alerts Section
    if not df.empty and not budgets_df.empty:
        current_month = date.today().strftime("%Y-%m")
        monthly_expenses = df[(df["type"] == "Expense") & (df["date"].str.startswith(current_month))]
        cat_spending = monthly_expenses.groupby("category")["amount"].sum().reset_index()
        merged_budgets = pd.merge(budgets_df, cat_spending, on="category", how="left").fillna(0)

        for _, row in merged_budgets.iterrows():
            pct = (row["amount"] / row["monthly_limit"]) * 100
            if pct >= 100:
                st.error(f"🚨 **Budget Exceeded:** You spent ₹{row['amount']:,.2f} on **{row['category']}** (Limit: ₹{row['monthly_limit']:,.2f}).")
            elif pct >= 80:
                st.warning(f"⚠️ **Budget Alert:** You have used {pct:.0f}% of your **{row['category']}** budget (₹{row['amount']:,.2f} / ₹{row['monthly_limit']:,.2f}).")

    st.divider()

    # Add Transaction & Bulk CSV Upload
    col_form, col_charts = st.columns([1, 2])

    with col_form:
        st.subheader("Add Transaction")
        with st.form("transaction_form", clear_on_submit=True):
            t_date = st.date_input("Date", value=date.today())
            t_type = st.selectbox("Type", ["Expense", "Income"])
            t_desc = st.text_input("Description (e.g., Swiggy order, Metro card)")
            t_cat = st.selectbox("Category (Leave 'Auto' to detect from description)", ["Auto"] + CATEGORIES)
            t_amount = st.number_input("Amount (₹)", min_value=1.0, step=50.0)
            
            if st.form_submit_button("Add Record"):
                final_cat = utils.auto_categorize(t_desc) if t_cat == "Auto" else t_cat
                if t_type == "Income" and t_cat == "Auto":
                    final_cat = "Salary/Allowance"
                db.add_transaction(st.session_state.user_id, t_date, t_type, final_cat, t_amount, t_desc)
                st.success(f"Added under '{final_cat}'!")
                st.rerun()

        st.subheader("Import Bank Statement (CSV)")
        uploaded_file = st.file_uploader("Upload CSV (Columns: date, type, amount, description)", type=["csv"])
        if uploaded_file is not None:
            if st.button("Process CSV"):
                try:
                    csv_df = pd.read_csv(uploaded_file)
                    for _, r in csv_df.iterrows():
                        cat = utils.auto_categorize(str(r.get("description", "")))
                        db.add_transaction(
                            st.session_state.user_id,
                            r["date"],
                            r["type"],
                            cat,
                            float(r["amount"]),
                            str(r.get("description", ""))
                        )
                    st.success("CSV imported successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error parsing CSV: {e}")

    with col_charts:
        st.subheader("Spending Analytics")
        if df.empty:
            st.info("No transactions yet. Add your first expense or income on the left to generate charts.")
        else:
            exp_df = df[df["type"] == "Expense"]
            if not exp_df.empty:
                fig_pie = px.pie(
                    exp_df, values="amount", names="category",
                    title="Expense Breakdown by Category", hole=0.4
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)
            trend_df = df.groupby(["month", "type"])["amount"].sum().reset_index()
            fig_bar = px.bar(
                trend_df, x="month", y="amount", color="type", barmode="group",
                title="Monthly Income vs. Expenses"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # Transaction History & Export
    st.subheader("Transaction History")
    if not df.empty:
        display_df = df.drop(columns=["month"], errors="ignore")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        col_exp, col_del = st.columns([1, 2])
        with col_exp:
            csv_data = display_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Report as CSV",
                data=csv_data,
                file_name="financial_report.csv",
                mime="text/csv"
            )
        with col_del:
            del_id = st.number_input("Enter Transaction ID to Delete", min_value=1, step=1)
            if st.button("Delete Transaction"):
                db.delete_transaction(del_id, st.session_state.user_id)
                st.success(f"Deleted transaction #{del_id}")
                st.rerun()

if st.session_state.user_id is None:
    auth_page()
else:
    main_dashboard()
