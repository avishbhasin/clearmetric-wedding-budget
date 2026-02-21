"""
Wedding Budget Planner — Free Web Tool by ClearMetric
https://clearmetric.gumroad.com

Product T9. Helps couples plan their wedding budget with realistic cost breakdowns.
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Wedding Budget Planner — ClearMetric",
    page_icon="💍",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS (navy theme)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main .block-container { padding-top: 2rem; max-width: 1200px; }
    .stMetric { background: #f8f9fa; border-radius: 8px; padding: 12px; border-left: 4px solid #2C3E50; }
    h1 { color: #2C3E50; }
    h2, h3 { color: #1C2833; }
    .rule-pass { color: #27ae60; font-weight: bold; }
    .rule-fail { color: #e74c3c; font-weight: bold; }
    .cta-box {
        background: linear-gradient(135deg, #2C3E50 0%, #1C2833 100%);
        color: white; padding: 24px; border-radius: 12px; text-align: center;
        margin: 20px 0;
    }
    .cta-box a { color: #D5D8DC; text-decoration: none; font-weight: bold; font-size: 1.1rem; }
    div[data-testid="stSidebar"] { background: #f8f9fa; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
NATIONAL_AVG_2025 = 33_000
REGIONS = ["Northeast", "Southeast", "Midwest", "West Coast", "South"]
REGION_MULTIPLIERS = {
    "Northeast": 1.15,
    "Southeast": 0.95,
    "Midwest": 0.90,
    "West Coast": 1.20,
    "South": 0.85,
}
SEASONS = ["Spring", "Summer", "Fall", "Winter"]
SEASON_MULTIPLIERS = {
    "Spring": 1.10,
    "Summer": 1.15,
    "Fall": 1.05,
    "Winter": 0.90,
    "Off-season": 0.85,
}
STANDARD_PERCENTAGES = {
    "Venue & Catering": 45,
    "Photography/Video": 12,
    "Music/DJ": 7,
    "Flowers & Decor": 8,
    "Attire & Beauty": 8,
    "Stationery & Invites": 3,
    "Transportation": 3,
    "Favors & Gifts": 2,
    "Officiant": 1,
    "Miscellaneous/Buffer": 11,
}
CATEGORIES = list(STANDARD_PERCENTAGES.keys())
# Typical ranges for "over/under" (as % of total)
CATEGORY_RANGES = {
    "Venue & Catering": (40, 50),
    "Photography/Video": (10, 15),
    "Music/DJ": (5, 10),
    "Flowers & Decor": (6, 12),
    "Attire & Beauty": (5, 10),
    "Stationery & Invites": (2, 5),
    "Transportation": (2, 5),
    "Favors & Gifts": (1, 4),
    "Officiant": (0.5, 2),
    "Miscellaneous/Buffer": (8, 15),
}

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("# 💍 Wedding Budget Planner")
st.markdown("**Plan your wedding budget with realistic cost breakdowns.** Compare to national averages and find where to save.")
st.markdown("---")

# ---------------------------------------------------------------------------
# Sidebar — User inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## Your Wedding Details")

    total_budget = st.number_input(
        "Total Wedding Budget ($)",
        value=30_000,
        min_value=1_000,
        max_value=500_000,
        step=1_000,
        format="%d",
    )
    num_guests = st.number_input(
        "Number of Guests",
        value=120,
        min_value=10,
        max_value=500,
        step=1,
        format="%d",
    )
    wedding_region = st.selectbox(
        "Wedding Region",
        REGIONS,
        index=0,
    )
    season = st.selectbox(
        "Season",
        SEASONS,
        index=1,
    )
    per_guest_estimate = st.number_input(
        "Per-Guest Cost Estimate ($)",
        value=250,
        min_value=50,
        max_value=500,
        step=25,
        format="%d",
        help="National average ~$250. Affects food/drink benchmark.",
    )
    whos_paying = st.selectbox(
        "Who's Paying?",
        ["Couple only", "Parents contributing", "Split"],
        index=0,
    )
    parents_contribution = st.number_input(
        "Parents Contribution ($)",
        value=0,
        min_value=0,
        max_value=200_000,
        step=1_000,
        format="%d",
    )

    st.markdown("### Budget Allocation")
    allocation_method = st.radio(
        "Allocation Method",
        ["Use standard percentages", "Custom"],
        index=0,
    )

    if allocation_method == "Use standard percentages":
        pct_dict = STANDARD_PERCENTAGES.copy()
    else:
        st.caption("Adjust sliders. Total must sum to 100%.")
        pct_dict = {}
        for cat in CATEGORIES:
            default = STANDARD_PERCENTAGES[cat]
            pct_dict[cat] = st.slider(cat, 0, 30, default, 1)
        total_pct = sum(pct_dict.values())
        if abs(total_pct - 100) > 0.5:
            st.warning(f"Total: {total_pct}% — Adjust to 100% or we'll normalize.")
            # Normalize so percentages sum to 100
            if total_pct > 0:
                pct_dict = {k: v / total_pct * 100 for k, v in pct_dict.items()}

# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------
budget_per_guest = total_budget / num_guests if num_guests > 0 else 0

# Allocation by category
allocation = {cat: total_budget * (pct / 100) for cat, pct in pct_dict.items()}

# Regional average
region_mult = REGION_MULTIPLIERS.get(wedding_region, 1.0)
season_mult = SEASON_MULTIPLIERS.get(season, 1.0)
regional_avg = NATIONAL_AVG_2025 * region_mult * season_mult

# Per-category: are you over/under typical range?
over_under = {}
for cat in CATEGORIES:
    pct = pct_dict.get(cat, 0)
    lo, hi = CATEGORY_RANGES.get(cat, (0, 20))
    if pct < lo:
        over_under[cat] = "under"
    elif pct > hi:
        over_under[cat] = "over"
    else:
        over_under[cat] = "typical"

# Guest cost analysis
venue_catering = allocation.get("Venue & Catering", 0)
per_guest_spend = venue_catering / num_guests if num_guests > 0 else 0

# Buffer amount
buffer_amount = allocation.get("Miscellaneous/Buffer", 0)

# Savings opportunities: categories with biggest flex (typically flowers, favors, stationery)
FLEX_CATEGORIES = ["Flowers & Decor", "Favors & Gifts", "Stationery & Invites", "Transportation"]
savings_opps = []
for cat in FLEX_CATEGORIES:
    amt = allocation.get(cat, 0)
    lo, _ = CATEGORY_RANGES.get(cat, (0, 20))
    if amt > 0:
        potential_save = amt * 0.2  # 20% flex
        savings_opps.append((cat, amt, potential_save))
savings_opps.sort(key=lambda x: x[2], reverse=True)

# Biggest expense
biggest_expense = max(allocation.items(), key=lambda x: x[1]) if allocation else ("", 0)

# ---------------------------------------------------------------------------
# Display — Key metrics
# ---------------------------------------------------------------------------
st.markdown("## Key Results")

m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "Budget per Guest",
    f"${budget_per_guest:,.0f}",
    help="Total budget ÷ number of guests",
)
m2.metric(
    "Biggest Expense",
    f"${biggest_expense[1]:,.0f}" if biggest_expense[0] else "—",
    biggest_expense[0] or "",
)
m3.metric(
    "Buffer Amount",
    f"${buffer_amount:,.0f}",
    help="Miscellaneous / contingency reserve",
)
vs_national = ((total_budget - NATIONAL_AVG_2025) / NATIONAL_AVG_2025 * 100) if NATIONAL_AVG_2025 else 0
m4.metric(
    "vs National Avg",
    f"{vs_national:+.0f}%",
    help=f"National avg 2025: ${NATIONAL_AVG_2025:,}",
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Donut chart — Budget allocation
# ---------------------------------------------------------------------------
st.markdown("## Budget Allocation")

fig_donut = go.Figure(
    data=[
        go.Pie(
            labels=list(allocation.keys()),
            values=list(allocation.values()),
            hole=0.5,
            marker_colors=[
                "#8E3553", "#B85C7A", "#D4849A", "#E8A8B8", "#F9E4EC",
                "#F9D4E0", "#F9C4D4", "#F9B4C8", "#F9A4BC", "#E8A8B8",
            ][: len(CATEGORIES)],
        )
    ]
)
fig_donut.update_layout(
    height=450,
    showlegend=True,
    legend=dict(orientation="h", y=1.02),
    margin=dict(t=40, b=40),
)
st.plotly_chart(fig_donut, use_container_width=True)

# ---------------------------------------------------------------------------
# Horizontal bar — Your budget vs national avg by category
# ---------------------------------------------------------------------------
st.markdown("## Your Budget vs National Average by Category")

# National avg allocation by category
national_allocation = {cat: NATIONAL_AVG_2025 * (pct / 100) for cat, pct in STANDARD_PERCENTAGES.items()}
regional_allocation = {cat: regional_avg * (pct / 100) for cat, pct in STANDARD_PERCENTAGES.items()}

df_compare = pd.DataFrame({
    "Category": CATEGORIES,
    "Your Budget": [allocation.get(c, 0) for c in CATEGORIES],
    "National Avg": [national_allocation.get(c, 0) for c in CATEGORIES],
    "Regional Avg": [regional_allocation.get(c, 0) for c in CATEGORIES],
})

fig_bar = go.Figure()
fig_bar.add_trace(
    go.Bar(
        name="Your Budget",
        y=df_compare["Category"],
        x=df_compare["Your Budget"],
        orientation="h",
        marker_color="#8E3553",
    )
)
fig_bar.add_trace(
    go.Bar(
        name="National Avg",
        y=df_compare["Category"],
        x=df_compare["National Avg"],
        orientation="h",
        marker_color="#AEB6BF",
    )
)
fig_bar.update_layout(
    barmode="group",
    height=500,
    xaxis_title="Amount ($)",
    xaxis_tickformat="$,.0f",
    margin=dict(t=40, b=40),
    legend=dict(orientation="h", y=1.02),
)
st.plotly_chart(fig_bar, use_container_width=True)

# ---------------------------------------------------------------------------
# Guest count impact slider
# ---------------------------------------------------------------------------
st.markdown("## Guest Count Impact")

guest_slider = st.slider(
    "Adjust guest count to see impact on budget per guest",
    min_value=50,
    max_value=300,
    value=num_guests,
    step=10,
)
if guest_slider > 0:
    impact_per_guest = total_budget / guest_slider
    st.info(
        f"At **{guest_slider} guests**, your budget per guest would be **${impact_per_guest:,.0f}**. "
        f"Fewer guests = more spending per person; more guests = more total cost."
    )

# ---------------------------------------------------------------------------
# Where to save recommendations
# ---------------------------------------------------------------------------
st.markdown("## Where to Save")

if savings_opps:
    for cat, amt, potential in savings_opps[:4]:
        st.markdown(f"- **{cat}** (${amt:,.0f}): Consider trimming ~20% → save ~${potential:,.0f}")
else:
    st.markdown("Your allocation looks balanced. Focus on negotiating with vendors for your top categories.")

# Per-category status
st.markdown("### Per-Category Status")
status_df = pd.DataFrame([
    {"Category": cat, "Your %": f"{pct_dict.get(cat, 0):.1f}%", "Status": over_under.get(cat, "—")}
    for cat in CATEGORIES
])
st.dataframe(status_df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# CTA — Paid Excel
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("""
<div class="cta-box">
    <h3 style="color: white; margin: 0 0 8px 0;">Want the Full Excel Spreadsheet?</h3>
    <p style="margin: 0 0 16px 0;">
        Get the <strong>ClearMetric Wedding Budget Planner</strong> — $14.99<br>
        ✓ Budget Planner with budgeted vs actual tracking<br>
        ✓ Vendor Tracker — quoted price, deposits, balance, due dates<br>
        ✓ How To Use guide<br>
    </p>
    <a href="https://clearmetric.gumroad.com/l/wedding-budget-planner" target="_blank">
        Get It on Gumroad — $14.99 →
    </a>
</div>
""", unsafe_allow_html=True)

# Cross-sell Budget Planner
st.markdown("### More from ClearMetric")
cx1, cx2, cx3 = st.columns(3)
with cx1:
    st.markdown("""
    **📊 Budget Planner** — $13.99
    Track income, expenses, savings with the 50/30/20 framework.
    [Get it →](https://clearmetric.gumroad.com/l/budget-planner)
    """)
with cx2:
    st.markdown("""
    **🚗 Car Affordability** — $9.99
    20/4/10 rule, total cost of ownership.
    [Get it →](https://clearmetric.gumroad.com/l/car-affordability-calculator)
    """)
with cx3:
    st.markdown("""
    **🔥 FIRE Calculator** — $14.99
    Find your FIRE number, scenario comparison.
    [Get it →](https://clearmetric.gumroad.com)
    """)

# Footer
st.markdown("---")
st.caption(
    "© 2026 ClearMetric | [clearmetric.gumroad.com](https://clearmetric.gumroad.com) | "
    "This tool is for educational purposes only. Not financial advice."
)
