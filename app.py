import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from supabase import create_client, Client

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CONFIGURATION
# ============================================================

CATEGORIES = [
    "Food",
    "Coffee",
    "Cigarettes",
    "Gym",
    "Supplements",
    "Transportation",
    "Shopping",
    "Entertainment",
    "Education",
    "Bills",
    "Installment",
    "Other",
]

INCOME_CATEGORY = "Salary"

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
        .block-container {
            max-width: 760px;
            padding-top: 1rem;
            padding-bottom: 4rem;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.35rem;
        }

        .stButton button {
            border-radius: 12px;
            min-height: 44px;
        }

        div[data-baseweb="select"] > div {
            border-radius: 10px;
        }

        input,
        textarea {
            border-radius: 10px !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# SUPABASE CONNECTION
# ============================================================

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]

    return create_client(url, key)


try:
    supabase = get_supabase()

except Exception:
    st.error(
        "Could not connect to Supabase. "
        "Please check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
        "in your Streamlit secrets."
    )
    st.stop()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_money(amount):
    try:
        return f"{int(round(float(amount))):,} Toman"
    except Exception:
        return "0 Toman"


def fetch_transactions():
    response = (
        supabase
        .table("transactions")
        .select("*")
        .order("transaction_date", desc=True)
        .order("id", desc=True)
        .execute()
    )

    df = pd.DataFrame(response.data or [])

    if df.empty:
        return pd.DataFrame(
            columns=[
                "id",
                "type",
                "amount",
                "category",
                "transaction_date",
                "description",
                "created_at",
            ]
        )

    df["amount"] = pd.to_numeric(df["amount"])

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"]
    ).dt.date

    return df


def add_transaction(
    transaction_type,
    amount,
    category,
    transaction_date,
    description,
):
    payload = {
        "type": transaction_type,
        "amount": int(amount),
        "category": category,
        "transaction_date": transaction_date.isoformat(),
        "description": description.strip(),
    }

    supabase.table("transactions").insert(payload).execute()


def update_transaction(
    transaction_id,
    transaction_type,
    amount,
    category,
    transaction_date,
    description,
):
    payload = {
        "type": transaction_type,
        "amount": int(amount),
        "category": category,
        "transaction_date": transaction_date.isoformat(),
        "description": description.strip(),
    }

    (
        supabase
        .table("transactions")
        .update(payload)
        .eq("id", int(transaction_id))
        .execute()
    )


def delete_transaction(transaction_id):
    (
        supabase
        .table("transactions")
        .delete()
        .eq("id", int(transaction_id))
        .execute()
    )


def get_month_options(df):
    if df.empty:
        months = []
    else:
        months = sorted(
            df["transaction_date"]
            .dropna()
            .map(lambda x: x.strftime("%Y-%m"))
            .unique(),
            reverse=True,
        )

    current_month = date.today().strftime("%Y-%m")

    if current_month not in months:
        months = [current_month] + list(months)

    return months


def month_label(year_month):
    year, month = year_month.split("-")

    month_names = {
        "01": "January",
        "02": "February",
        "03": "March",
        "04": "April",
        "05": "May",
        "06": "June",
        "07": "July",
        "08": "August",
        "09": "September",
        "10": "October",
        "11": "November",
        "12": "December",
    }

    return f"{month_names[month]} {year}"


def filter_by_month(df, selected_month):
    if df.empty:
        return df

    return df[
        df["transaction_date"].map(
            lambda x: x.strftime("%Y-%m") == selected_month
        )
    ]


# ============================================================
# LOAD DATA
# ============================================================

df = fetch_transactions()

# ============================================================
# HEADER
# ============================================================

st.title("💰 Expense Tracker")

st.caption("Simple and minimal personal finance tracker")

# ============================================================
# TABS
# ============================================================

tab_dashboard, tab_add, tab_transactions, tab_reports = st.tabs(
    [
        "Dashboard",
        "＋ Add",
        "Transactions",
        "Reports",
    ]
)

# ============================================================
# DASHBOARD
# ============================================================

with tab_dashboard:

    month_options = get_month_options(df)

    selected_month = st.selectbox(
        "Month",
        month_options,
        format_func=month_label,
        key="dashboard_month",
    )

    month_df = filter_by_month(df, selected_month)

    income = month_df.loc[
        month_df["type"] == "income",
        "amount",
    ].sum()

    expenses = month_df.loc[
        month_df["type"] == "expense",
        "amount",
    ].sum()

    balance = income - expenses

    savings_rate = (
        (balance / income) * 100
        if income > 0
        else 0
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Income",
            format_money(income),
        )

    with col2:
        st.metric(
            "Expenses",
            format_money(expenses),
        )

    st.metric(
        "Balance",
        format_money(balance),
    )

    st.caption(
        f"Savings rate: {savings_rate:.1f}%"
    )

    # --------------------------------------------------------
    # EXPENSE BREAKDOWN
    # --------------------------------------------------------

    if not month_df.empty:

        expenses_df = month_df[
            month_df["type"] == "expense"
        ].copy()

        if not expenses_df.empty:

            category_totals = (
                expenses_df
                .groupby(
                    "category",
                    as_index=False,
                )["amount"]
                .sum()
                .sort_values(
                    "amount",
                    ascending=False,
                )
            )

            st.subheader(
                "Expenses by Category"
            )

            for _, row in category_totals.iterrows():

                st.write(
                    f"**{row['category']}** — "
                    f"{format_money(row['amount'])}"
                )

            fig = px.pie(
                category_totals,
                names="category",
                values="amount",
                hole=0.55,
            )

            fig.update_layout(
                margin=dict(
                    l=10,
                    r=10,
                    t=20,
                    b=10,
                ),
                legend_title_text="Category",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

            # ------------------------------------------------
            # RECENT TRANSACTIONS
            # ------------------------------------------------

            st.subheader(
                "Recent Transactions"
            )

            recent = month_df.head(8).copy()

            recent["Type"] = recent["type"].map(
                {
                    "income": "Income",
                    "expense": "Expense",
                }
            )

            recent["Amount"] = recent[
                "amount"
            ].map(format_money)

            recent["Date"] = recent[
                "transaction_date"
            ].astype(str)

            recent["Category"] = recent[
                "category"
            ]

            recent["Description"] = recent[
                "description"
            ]

            st.dataframe(
                recent[
                    [
                        "Date",
                        "Type",
                        "Category",
                        "Amount",
                        "Description",
                    ]
                ],
                hide_index=True,
                use_container_width=True,
            )

        else:

            st.info(
                "No expenses have been recorded "
                "for this month yet."
            )

    else:

        st.info(
            "No transactions have been recorded "
            "for this month."
        )


# ============================================================
# ADD TRANSACTION
# ============================================================

with tab_add:

    st.subheader(
        "Add Transaction"
    )

    transaction_type_label = st.radio(
        "Type",
        [
            "Expense",
            "Income",
        ],
        horizontal=True,
    )

    transaction_type = (
        "expense"
        if transaction_type_label == "Expense"
        else "income"
    )

    amount = st.number_input(
        "Amount (Toman)",
        min_value=0,
        step=10_000,
        value=0,
        format="%d",
    )

    if transaction_type == "expense":

        category = st.selectbox(
            "Category",
            CATEGORIES,
        )

    else:

        category = INCOME_CATEGORY

    transaction_date = st.date_input(
        "Date",
        value=date.today(),
    )

    description = st.text_input(
        "Description",
        placeholder=(
            "e.g. lunch, coffee, monthly salary..."
        ),
    )

    if st.button(
        "Add Transaction",
        type="primary",
        use_container_width=True,
    ):

        if amount <= 0:

            st.warning(
                "Amount must be greater than zero."
            )

        else:

            try:

                add_transaction(
                    transaction_type,
                    amount,
                    category,
                    transaction_date,
                    description,
                )

                st.success(
                    "Transaction added successfully."
                )

                st.rerun()

            except Exception as error:

                st.error(
                    f"Could not add transaction: {error}"
                )


# ============================================================
# TRANSACTIONS
# ============================================================

with tab_transactions:

    st.subheader(
        "Transactions"
    )

    if df.empty:

        st.info(
            "No transactions yet."
        )

    else:

        col1, col2 = st.columns(2)

        with col1:

            search = st.text_input(
                "Search",
                placeholder="e.g. coffee",
            )

        with col2:

            type_filter = st.selectbox(
                "Type",
                [
                    "All",
                    "Expense",
                    "Income",
                ],
            )

        filtered_df = df.copy()

        # Search
        if search:

            search_mask = (
                filtered_df[
                    "category"
                ]
                .fillna("")
                .str.contains(
                    search,
                    case=False,
                    na=False,
                )
                |
                filtered_df[
                    "description"
                ]
                .fillna("")
                .str.contains(
                    search,
                    case=False,
                    na=False,
                )
            )

            filtered_df = filtered_df[
                search_mask
            ]

        # Type filter
        if type_filter != "All":

            wanted_type = (
                "expense"
                if type_filter == "Expense"
                else "income"
            )

            filtered_df = filtered_df[
                filtered_df["type"]
                == wanted_type
            ]

        st.caption(
            f"{len(filtered_df)} transaction(s)"
        )

        for _, row in filtered_df.iterrows():

            icon = (
                "🔴"
                if row["type"] == "expense"
                else "🟢"
            )

            with st.expander(
                f"{icon} "
                f"{row['category']} — "
                f"{format_money(row['amount'])} — "
                f"{row['transaction_date']}"
            ):

                st.write(
                    row["description"]
                    if row["description"]
                    else "No description"
                )

                # ------------------------------------------------
                # EDIT FORM
                # ------------------------------------------------

                with st.form(
                    f"edit_{row['id']}"
                ):

                    current_type = (
                        "Expense"
                        if row["type"] == "expense"
                        else "Income"
                    )

                    edit_type_label = st.radio(
                        "Type",
                        [
                            "Expense",
                            "Income",
                        ],
                        index=(
                            0
                            if current_type == "Expense"
                            else 1
                        ),
                        horizontal=True,
                        key=f"type_{row['id']}",
                    )

                    edit_type = (
                        "expense"
                        if edit_type_label == "Expense"
                        else "income"
                    )

                    edit_amount = st.number_input(
                        "Amount (Toman)",
                        min_value=0,
                        value=int(row["amount"]),
                        step=10_000,
                        key=f"amount_{row['id']}",
                    )

                    if edit_type == "expense":

                        current_category = (
                            row["category"]
                            if row["category"]
                            in CATEGORIES
                            else "Other"
                        )

                        category_index = (
                            CATEGORIES.index(
                                current_category
                            )
                        )

                        edit_category = st.selectbox(
                            "Category",
                            CATEGORIES,
                            index=category_index,
                            key=f"category_{row['id']}",
                        )

                    else:

                        edit_category = (
                            INCOME_CATEGORY
                        )

                    edit_date = st.date_input(
                        "Date",
                        value=row[
                            "transaction_date"
                        ],
                        key=f"date_{row['id']}",
                    )

                    edit_description = st.text_input(
                        "Description",
                        value=(
                            row["description"]
                            or ""
                        ),
                        key=f"description_{row['id']}",
                    )

                    save_changes = (
                        st.form_submit_button(
                            "Save Changes",
                            use_container_width=True,
                        )
                    )

                    if save_changes:

                        if edit_amount <= 0:

                            st.warning(
                                "Amount must be greater than zero."
                            )

                        else:

                            try:

                                update_transaction(
                                    row["id"],
                                    edit_type,
                                    edit_amount,
                                    edit_category,
                                    edit_date,
                                    edit_description,
                                )

                                st.success(
                                    "Changes saved successfully."
                                )

                                st.rerun()

                            except Exception as error:

                                st.error(
                                    "Could not update transaction: "
                                    f"{error}"
                                )

                # ------------------------------------------------
                # DELETE
                # ------------------------------------------------

                if st.button(
                    "Delete This Transaction",
                    key=f"delete_{row['id']}",
                    use_container_width=True,
                ):

                    try:

                        delete_transaction(
                            row["id"]
                        )

                        st.success(
                            "Transaction deleted successfully."
                        )

                        st.rerun()

                    except Exception as error:

                        st.error(
                            "Could not delete transaction: "
                            f"{error}"
                        )


# ============================================================
# REPORTS
# ============================================================

with tab_reports:

    st.subheader(
        "Reports"
    )

    if df.empty:

        st.info(
            "Add some transactions to generate reports."
        )

    else:

        reports_df = df.copy()

        reports_df["month"] = (
            reports_df[
                "transaction_date"
            ]
            .map(
                lambda x:
                x.strftime("%Y-%m")
            )
        )

        # --------------------------------------------------------
        # MONTHLY SUMMARY
        # --------------------------------------------------------

        monthly = (
            reports_df
            .pivot_table(
                index="month",
                columns="type",
                values="amount",
                aggfunc="sum",
                fill_value=0,
            )
            .reset_index()
        )

        if "income" not in monthly.columns:
            monthly["income"] = 0

        if "expense" not in monthly.columns:
            monthly["expense"] = 0

        monthly["balance"] = (
            monthly["income"]
            - monthly["expense"]
        )

        st.subheader(
            "Monthly Comparison"
        )

        chart_df = monthly.melt(
            id_vars="month",
            value_vars=[
                "income",
                "expense",
                "balance",
            ],
            var_name="Type",
            value_name="Amount",
        )

        chart_df["Type"] = chart_df[
            "Type"
        ].map(
            {
                "income": "Income",
                "expense": "Expenses",
                "balance": "Balance",
            }
        )

        monthly_fig = px.bar(
            chart_df,
            x="month",
            y="Amount",
            color="Type",
            barmode="group",
        )

        monthly_fig.update_layout(
            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10,
            )
        )

        st.plotly_chart(
            monthly_fig,
            use_container_width=True,
        )

        # --------------------------------------------------------
        # DAILY EXPENSE TREND
        # --------------------------------------------------------

        st.subheader(
            "Daily Expense Trend"
        )

        daily = (
            reports_df[
                reports_df["type"]
                == "expense"
            ]
            .groupby(
                "transaction_date",
                as_index=False,
            )["amount"]
            .sum()
            .sort_values(
                "transaction_date"
            )
        )

        if not daily.empty:

            daily_fig = px.line(
                daily,
                x="transaction_date",
                y="amount",
                markers=True,
            )

            daily_fig.update_layout(
                margin=dict(
                    l=10,
                    r=10,
                    t=20,
                    b=10,
                ),
                yaxis_title="Amount (Toman)",
                xaxis_title="Date",
            )

            st.plotly_chart(
                daily_fig,
                use_container_width=True,
            )

        # --------------------------------------------------------
        # AVERAGE DAILY EXPENSE
        # --------------------------------------------------------

        st.subheader(
            "Average Daily Expense"
        )

        if not daily.empty:

            average_daily = (
                daily["amount"].mean()
            )

            st.metric(
                "Average on Days With Expenses",
                format_money(
                    average_daily
                ),
            )

        # --------------------------------------------------------
        # TOP EXPENSE CATEGORIES
        # --------------------------------------------------------

        st.subheader(
            "Top Expense Categories"
        )

        top_categories = (
            reports_df[
                reports_df["type"]
                == "expense"
            ]
            .groupby(
                "category",
                as_index=False,
            )["amount"]
            .sum()
            .sort_values(
                "amount",
                ascending=False,
            )
            .head(5)
        )

        top_categories_display = (
            top_categories.rename(
                columns={
                    "category": "Category",
                    "amount": "Amount",
                }
            )
        )

        st.dataframe(
            top_categories_display,
            hide_index=True,
            use_container_width=True,
        )

        # --------------------------------------------------------
        # EXPORT
        # --------------------------------------------------------

        st.subheader(
            "Export"
        )

        export_df = reports_df.drop(
            columns=["month"],
            errors="ignore",
        ).copy()

        export_df["type"] = export_df[
            "type"
        ].map(
            {
                "income": "Income",
                "expense": "Expense",
            }
        )

        export_df["amount"] = (
            export_df["amount"]
            .astype(int)
        )

        # CSV
        csv_data = (
            export_df
            .to_csv(
                index=False
            )
            .encode("utf-8-sig")
        )

        st.download_button(
            "Download CSV",
            data=csv_data,
            file_name="transactions.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # Excel
        excel_path = "/tmp/transactions.xlsx"

        export_df.to_excel(
            excel_path,
            index=False,
            engine="openpyxl",
        )

        with open(
            excel_path,
            "rb",
        ) as excel_file:

            st.download_button(
                "Download Excel",
                data=excel_file.read(),
                file_name="transactions.xlsx",
                mime=(
                    "application/"
                    "vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True,
            )