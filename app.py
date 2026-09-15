import streamlit as st
import pandas as pd
from rapidfuzz import fuzz

# ---------------------------------------------------------
# PAGE SETUP
# ---------------------------------------------------------

st.set_page_config(
    page_title="Plant-Based Grocery Basket",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------
# COLOURS / DATA
# ---------------------------------------------------------

NUTRIENT_COLOURS = {
    "IRON (mg)": "#D1007A",
    "IODINE (µg)": "#8FD3FF",
    "B12 (µg)": "#4CAF50",
    "CALCIUM (mg)": "#F4D35E",
    "OMEGA3 ALA (mg)": "#C47A32",
}

NUTRIENT_NAMES = {
    "IRON (mg)": "Iron",
    "B12 (µg)": "Vitamin B12",
    "IODINE (µg)": "Iodine",
    "CALCIUM (mg)": "Calcium",
    "OMEGA3 ALA (mg)": "Omega-3 ALA",
}

NUTRIENT_ICONS = {
    "IRON (mg)": "🩸",
    "B12 (µg)": "🌱",
    "IODINE (µg)": "💧",
    "CALCIUM (mg)": "🦴",
    "OMEGA3 ALA (mg)": "🫒",
}

targets = {
    "IRON (mg)": 18,
    "B12 (µg)": 2.4,
    "IODINE (µg)": 150,
    "CALCIUM (mg)": 1000,
    "OMEGA3 ALA (mg)": 1100,
}

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

foods = pd.read_csv("foods.csv")
foods["Product ID"] = foods.index

if "OMEGA3 ALA (mg)" not in foods.columns:
    if "OMEGA3 (mg)" in foods.columns:
        foods["OMEGA3 ALA (mg)"] = foods["OMEGA3 (mg)"]
    else:
        foods["OMEGA3 ALA (mg)"] = 0

for nutrient in targets:
    if nutrient not in foods.columns:
        foods[nutrient] = 0
    foods[nutrient] = pd.to_numeric(
        foods[nutrient], errors="coerce"
    ).fillna(0)

for column in ["Brand", "Product", "Package Size", "Serving Size",
               "Retailer", "Category", "VEGAN"]:
    if column not in foods.columns:
        foods[column] = ""

if "Image URL" not in foods.columns:
    foods["Image URL"] = ""

foods["Image URL"] = foods["Image URL"].fillna("").astype(str)

# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

defaults = {
    "basket": {},
    "nutrient_focus": None,
    "page": 1,
    "ribbon_category": "All",
    "screen": "Catalogue",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------------------------------------------------
# MOBILE-FIRST CSS
# ---------------------------------------------------------

st.markdown(
    """
    <style>
    /* ---------- Global ---------- */

    .stApp {
        background: #F6F7F2;
    }

    [data-testid="stAppViewContainer"] {
        background: #F6F7F2;
    }

    .main .block-container {
        max-width: 1180px;
        padding-top: 1.1rem;
        padding-bottom: 6.5rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* Hide the sidebar completely on small screens */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] {
            display: none;
        }

        .main .block-container {
            padding-top: 0.65rem;
            padding-left: 0.72rem;
            padding-right: 0.72rem;
            padding-bottom: 5.8rem;
        }
    }

    /* ---------- Typography ---------- */

    h1 {
        letter-spacing: -1.4px;
        margin-bottom: 0.15rem !important;
    }

    h2, h3 {
        letter-spacing: -0.5px;
    }

    /* ---------- Search / controls ---------- */

    div[data-testid="stTextInput"] input {
        border-radius: 16px !important;
        border: 1px solid #DDE1D9 !important;
        background: #FFFFFF !important;
        min-height: 46px !important;
    }

    div[data-testid="stSelectbox"] > div > div {
        border-radius: 13px !important;
        border-color: #DDE1D9 !important;
        background: #FFFFFF !important;
    }

    div[data-testid="stRadio"] {
        background: #EDEFE8;
        padding: 4px 6px;
        border-radius: 14px;
    }

    div[data-testid="stRadio"] label {
        border-radius: 10px;
    }

    /* ---------- Streamlit containers / product cards ---------- */

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #E1E4DC !important;
        border-radius: 18px !important;
        background: #FFFFFF !important;
        box-shadow: 0 2px 9px rgba(35, 45, 35, 0.045);
        overflow: hidden;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 0.72rem !important;
    }

    @media (max-width: 768px) {
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 0.68rem !important;
        }
    }

    /* ---------- Product image ---------- */

    .product-thumb {
        width: 86px;
        height: 86px;
        border-radius: 14px;
        background: #F1F2EC;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        flex-shrink: 0;
        border: 1px solid #E6E8E0;
    }

    .product-thumb img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        background: #FFFFFF;
    }

    .product-thumb-placeholder {
        font-size: 28px;
        opacity: 0.55;
    }

    .product-top {
        display: flex;
        gap: 11px;
        align-items: flex-start;
        min-height: 86px;
    }

    .product-copy {
        min-width: 0;
        padding-top: 1px;
    }

    .brand {
        font-size: 0.68rem;
        font-weight: 800;
        color: #7A8077;
        text-transform: uppercase;
        letter-spacing: 0.45px;
        margin-bottom: 2px;
    }

    .product-name {
        font-size: 0.98rem;
        font-weight: 750;
        line-height: 1.18;
        color: #20241F;
        margin-bottom: 5px;
    }

    .product-meta {
        font-size: 0.69rem;
        line-height: 1.35;
        color: #777D75;
    }

    /* ---------- Nutrient mini bars ---------- */

    .nutrient-row {
        margin-top: 9px;
    }

    .nutrient-line {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.68rem;
        line-height: 1;
        margin-bottom: 4px;
        color: #535951;
    }

    .nutrient-value {
        color: #777D75;
        font-weight: 600;
    }

    .nutrient-track {
        width: 100%;
        height: 5px;
        background: #E9EBE5;
        border-radius: 99px;
        overflow: hidden;
    }

    .nutrient-fill {
        height: 5px;
        border-radius: 99px;
    }

    /* ---------- Buttons ---------- */

    div.stButton > button {
        border-radius: 12px !important;
        min-height: 42px !important;
        font-weight: 700 !important;
        border: 1px solid #DCE0D8 !important;
        background: #FFFFFF !important;
        color: #252A24 !important;
    }

    div.stButton > button:hover {
        border-color: #8E998B !important;
        background: #F7F8F4 !important;
    }

    /* Add buttons */
    .add-label {
        margin-top: 10px;
    }

    /* ---------- Category ribbon ---------- */

    .ribbon-title {
        font-size: 0.74rem;
        font-weight: 800;
        color: #6F756C;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin: 4px 0 7px 2px;
    }

    .ribbon-scroll {
        display: flex;
        gap: 7px;
        overflow-x: auto;
        padding: 2px 2px 7px 2px;
        scrollbar-width: none;
    }

    .ribbon-scroll::-webkit-scrollbar {
        display: none;
    }

    /* ---------- Basket dashboard ---------- */

    .basket-card {
        background: #FFFFFF;
        border: 1px solid #E1E4DC;
        border-radius: 18px;
        padding: 14px;
        margin-bottom: 10px;
        box-shadow: 0 2px 9px rgba(35, 45, 35, 0.04);
    }

    .basket-item-name {
        font-weight: 750;
        font-size: 0.91rem;
        line-height: 1.2;
    }

    .basket-item-meta {
        font-size: 0.7rem;
        color: #777D75;
        margin-top: 3px;
    }

    .dashboard-card {
        background: #FFFFFF;
        border: 1px solid #E1E4DC;
        border-radius: 18px;
        padding: 15px;
        margin-top: 12px;
        box-shadow: 0 2px 9px rgba(35, 45, 35, 0.04);
    }

    .dashboard-title {
        font-size: 0.78rem;
        font-weight: 800;
        color: #6F756C;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-bottom: 12px;
    }

    .big-nutrient {
        margin-bottom: 13px;
    }

    .big-nutrient-head {
        display: flex;
        justify-content: space-between;
        font-weight: 750;
        font-size: 0.83rem;
        margin-bottom: 5px;
    }

    .big-track {
        width: 100%;
        height: 12px;
        background: #E8EAE4;
        border-radius: 99px;
        overflow: hidden;
    }

    .big-fill {
        height: 12px;
        border-radius: 99px;
    }

    .big-detail {
        font-size: 0.69rem;
        color: #777D75;
        margin-top: 4px;
    }

    .insight-card {
        background: #F0F4EC;
        border: 1px solid #DCE6D7;
        border-radius: 16px;
        padding: 12px 13px;
        margin-top: 11px;
        font-size: 0.78rem;
        line-height: 1.4;
    }

    /* ---------- Empty state ---------- */

    .empty-card {
        background: #FFFFFF;
        border: 1px dashed #D8DDD4;
        border-radius: 18px;
        padding: 28px 18px;
        text-align: center;
        color: #70766D;
    }

    /* ---------- Floating basket ---------- */

    .floating-basket {
        position: fixed;
        left: 10px;
        right: 10px;
        bottom: 10px;
        z-index: 999999;
        background: rgba(32, 37, 31, 0.96);
        color: #FFFFFF;
        border-radius: 17px;
        padding: 9px 11px;
        box-shadow: 0 8px 28px rgba(0,0,0,0.20);
        backdrop-filter: blur(12px);
    }

    .floating-inner {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .floating-count {
        font-size: 0.72rem;
        color: #D9DED6;
        line-height: 1.1;
        min-width: 70px;
    }

    .floating-count strong {
        display: block;
        color: #FFFFFF;
        font-size: 0.88rem;
    }

    .floating-bars {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 4px;
        flex: 1;
    }

    .floating-track {
        height: 4px;
        background: #4D534B;
        border-radius: 99px;
        overflow: hidden;
    }

    .floating-fill {
        height: 4px;
        border-radius: 99px;
    }

    .floating-arrow {
        font-size: 0.72rem;
        font-weight: 800;
        white-space: nowrap;
        color: #FFFFFF;
    }

    /* ---------- Hide desktop-only extras on mobile ---------- */

    @media (max-width: 768px) {
        h1 {
            font-size: 1.65rem !important;
        }

        .product-top {
            min-height: 78px;
        }

        .product-thumb {
            width: 78px;
            height: 78px;
        }

        .product-name {
            font-size: 0.94rem;
        }

        .nutrient-row {
            margin-top: 7px;
        }

        .floating-basket {
            bottom: 8px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def add_to_basket(product_id, product_name):
    if product_id in st.session_state.basket:
        st.session_state.basket[product_id] += 1
    else:
        st.session_state.basket[product_id] = 1
    st.toast(f"{product_name} added ✓")
    st.rerun()


def clear_basket():
    st.session_state.basket = {}
    st.session_state.nutrient_focus = None
    st.rerun()


def calculate_totals():
    totals = {nutrient: 0.0 for nutrient in targets}

    for product_id, servings in st.session_state.basket.items():
        matches = foods[foods["Product ID"] == product_id]
        if len(matches) == 0:
            continue

        product = matches.iloc[0]

        for nutrient in targets:
            totals[nutrient] += float(product[nutrient]) * servings

    return totals


def nutrient_bar_html(nutrient, value, compact=True):
    target = targets[nutrient]
    percentage = (value / target) * 100 if target else 0
    display_percentage = min(max(percentage, 0), 100)
    colour = NUTRIENT_COLOURS[nutrient]
    name = NUTRIENT_NAMES[nutrient]
    icon = NUTRIENT_ICONS[nutrient]
    unit = "mg" if "(mg)" in nutrient else "µg"

    if compact:
        return f"""
        <div class="nutrient-row">
            <div class="nutrient-line">
                <span>{icon} {name}</span>
                <span class="nutrient-value">{percentage:.0f}%</span>
            </div>
            <div class="nutrient-track">
                <div class="nutrient-fill"
                     style="width:{display_percentage}%;background:{colour};"></div>
            </div>
        </div>
        """

    return f"""
    <div class="big-nutrient">
        <div class="big-nutrient-head">
            <span>{icon} {name}</span>
            <span>{percentage:.0f}%</span>
        </div>
        <div class="big-track">
            <div class="big-fill"
                 style="width:{display_percentage}%;background:{colour};"></div>
        </div>
        <div class="big-detail">
            {value:.1f} {unit} / {target} {unit} reference target
        </div>
    </div>
    """


# ---------------------------------------------------------
# TOP APP HEADER
# ---------------------------------------------------------

header_left, header_right = st.columns([4, 1])

with header_left:
    st.markdown(
        """
        <div style="font-size:0.7rem;font-weight:800;letter-spacing:1px;
                    color:#727A6E;text-transform:uppercase;margin-bottom:2px;">
            GROCERY NUTRITION
        </div>
        <h1 style="margin-top:0;">🌱 Plant Basket</h1>
        <div style="color:#70766D;font-size:0.86rem;margin-bottom:8px;">
            Build a basket and explore its contribution to key nutrients.
        </div>
        """,
        unsafe_allow_html=True,
    )

with header_right:
    st.metric(
        "Basket",
        f"{sum(st.session_state.basket.values())} serves",
    )

# ---------------------------------------------------------
# MOBILE APP NAVIGATION
# ---------------------------------------------------------

st.session_state.screen = st.radio(
    "App view",
    ["🛍️ Catalogue", "🛒 Basket"],
    index=0 if st.session_state.screen == "Catalogue" else 1,
    horizontal=True,
    label_visibility="collapsed",
)

# ---------------------------------------------------------
# BASKET VIEW
# ---------------------------------------------------------

if st.session_state.screen == "🛒 Basket":

    st.subheader("🛒 Your basket")

    if not st.session_state.basket:
        st.markdown(
            """
            <div class="empty-card">
                <div style="font-size:2rem;">🛒</div>
                <div style="font-weight:750;color:#30352F;margin-top:7px;">
                    Your basket is empty
                </div>
                <div style="font-size:0.78rem;margin-top:4px;">
                    Add foods from the catalogue to see your nutrient contribution.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for product_id, servings in list(st.session_state.basket.items()):
            product = foods[foods["Product ID"] == product_id].iloc[0]

            with st.container(border=True):
                left, middle, right = st.columns([4.8, 1.8, 1.2])

                with left:
                    st.html(
                        f"""
                        <div class="basket-item-name">
                            {product["Brand"]} · {product["Product"]}
                        </div>
                        <div class="basket-item-meta">
                            {product["Retailer"]} · {product["Serving Size"]}
                        </div>
                        """
                    )

                with middle:
                    new_servings = st.number_input(
                        "Serves",
                        min_value=1,
                        max_value=99,
                        value=int(servings),
                        step=1,
                        key=f"basket_servings_{product_id}",
                    )

                    if new_servings != servings:
                        st.session_state.basket[product_id] = new_servings
                        st.rerun()

                with right:
                    st.write("")
                    if st.button(
                        "✕",
                        key=f"remove_{product_id}",
                        help="Remove from basket",
                        use_container_width=True,
                    ):
                        del st.session_state.basket[product_id]
                        st.rerun()

        nutrient_totals = calculate_totals()

        st.html('<div class="dashboard-card">')
        st.html('<div class="dashboard-title">Your basket provides</div>')

        for nutrient in targets:
            st.html(
                nutrient_bar_html(
                    nutrient,
                    nutrient_totals[nutrient],
                    compact=False,
                )
            )

        st.html("</div>")

        coverage = {
            nutrient: nutrient_totals[nutrient] / targets[nutrient]
            for nutrient in targets
        }

        lowest_nutrient = min(coverage, key=coverage.get)
        lowest_percentage = coverage[lowest_nutrient] * 100

        st.html(
            f"""
            <div class="insight-card">
                💡 <strong>{NUTRIENT_NAMES[lowest_nutrient]}</strong>
                is currently your lowest-covered nutrient at approximately
                <strong>{lowest_percentage:.0f}%</strong> of the reference target.
            </div>
            """
        )

        if st.button(
            f"Find foods high in {NUTRIENT_NAMES[lowest_nutrient]}",
            use_container_width=True,
        ):
            st.session_state.nutrient_focus = lowest_nutrient
            st.session_state.page = 1
            st.session_state.screen = "Catalogue"
            st.rerun()

        if st.button("Clear basket", use_container_width=True):
            clear_basket()

# ---------------------------------------------------------
# CATALOGUE VIEW
# ---------------------------------------------------------

else:

    # Search
    search = st.text_input(
        "Search",
        placeholder="🔍  Search tofu, oats, Weet-Bix...",
        label_visibility="collapsed",
    )

    # Category ribbon
    st.html(
        '<div class="ribbon-title">Browse categories</div>'
    )

    category_options = [
        "All",
        "Dairy",
        "Pantry",
        "Vegetables",
        "Grains",
        "Legumes",
        "Nuts & Seeds",
        "Snacks",
    ]

    ribbon_cols = st.columns(4)

    for i, category in enumerate(category_options):
        with ribbon_cols[i % 4]:
            selected = st.session_state.ribbon_category == category

            if st.button(
                category,
                key=f"ribbon_{category}",
                use_container_width=True,
            ):
                st.session_state.ribbon_category = category
                st.session_state.page = 1
                st.rerun()

    # Search / filter
    filtered_foods = foods.copy()

    if search:
        search_clean = search.lower().strip()

        def fuzzy_match(product):
            product_clean = str(product).lower()

            if search_clean in product_clean:
                return True

            words = product_clean.replace("-", " ").split()

            for word in words:
                if fuzz.ratio(search_clean, word) >= 55:
                    return True

            return fuzz.partial_ratio(
                search_clean,
                product_clean,
            ) >= 55

        filtered_foods = filtered_foods[
            filtered_foods["Product"].astype(str).apply(fuzzy_match)
        ]

    # Compact filters
    filter_cols = st.columns(3)

    with filter_cols[0]:
        retailers = ["All"] + sorted(
            foods["Retailer"].dropna().unique().tolist()
        )
        retailer_filter = st.selectbox(
            "Retailer",
            retailers,
            label_visibility="collapsed",
        )

    with filter_cols[1]:
        categories = ["All"] + sorted(
            foods["Category"].dropna().unique().tolist()
        )
        category_filter = st.selectbox(
            "Category",
            categories,
            label_visibility="collapsed",
        )

    with filter_cols[2]:
        sort_options = {
            "Recommended": None,
            "Iron ↑": "IRON (mg)",
            "B12 ↑": "B12 (µg)",
            "Iodine ↑": "IODINE (µg)",
            "Calcium ↑": "CALCIUM (mg)",
            "Omega-3 ↑": "OMEGA3 ALA (mg)",
            "Name A–Z": "Product",
        }

        sort_choice = st.selectbox(
            "Sort",
            list(sort_options.keys()),
            label_visibility="collapsed",
        )

    vegan_only = st.checkbox(
        "🌱 Vegan products only",
    )

    if retailer_filter != "All":
        filtered_foods = filtered_foods[
            filtered_foods["Retailer"] == retailer_filter
        ]

    if category_filter != "All":
        filtered_foods = filtered_foods[
            filtered_foods["Category"] == category_filter
        ]

    if vegan_only:
        filtered_foods = filtered_foods[
            filtered_foods["VEGAN"].astype(str).str.upper() == "YES"
        ]

    if st.session_state.ribbon_category != "All":
        filtered_foods = filtered_foods[
            filtered_foods["Category"]
            .astype(str)
            .str.strip()
            .str.lower()
            == st.session_state.ribbon_category.lower()
        ]

    # Nutrient recommendation
    if st.session_state.nutrient_focus:
        nutrient = st.session_state.nutrient_focus

        positive_foods = filtered_foods[
            filtered_foods[nutrient] > 0
        ]

        if len(positive_foods) > 0:
            threshold = positive_foods[nutrient].median()
            filtered_foods = positive_foods[
                positive_foods[nutrient] >= threshold
            ].sort_values(
                nutrient,
                ascending=False,
            )

        st.info(
            f"Showing stronger sources of "
            f"{NUTRIENT_NAMES[nutrient]}. "
            f"Tap the button below to return to the full catalogue."
        )

        if st.button(
            "Show all foods",
            use_container_width=True,
        ):
            st.session_state.nutrient_focus = None
            st.session_state.page = 1
            st.rerun()

    else:
        sort_column = sort_options[sort_choice]

        if sort_column:
            filtered_foods = filtered_foods.sort_values(
                by=sort_column,
                ascending=(sort_column == "Product"),
                na_position="last",
            )

    # Catalogue heading
    st.markdown(
        f"""
        <div style="display:flex;justify-content:space-between;
                    align-items:end;margin:12px 2px 8px;">
            <div>
                <div style="font-size:1.08rem;font-weight:800;">
                    Grocery catalogue
                </div>
                <div style="font-size:0.7rem;color:#777D75;">
                    {len(filtered_foods)} products
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Pagination
    PRODUCTS_PER_PAGE = 8

    total_pages = max(
        1,
        (len(filtered_foods) + PRODUCTS_PER_PAGE - 1)
        // PRODUCTS_PER_PAGE,
    )

    if st.session_state.page > total_pages:
        st.session_state.page = total_pages

    start = (
        st.session_state.page - 1
    ) * PRODUCTS_PER_PAGE

    page_foods = filtered_foods.iloc[
        start:start + PRODUCTS_PER_PAGE
    ]

    if len(page_foods) == 0:
        st.markdown(
            """
            <div class="empty-card">
                🔎<br>
                <strong>No products found</strong><br>
                <span style="font-size:0.76rem;">
                    Try another search, retailer or category.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:
        # Two columns on larger screens; Streamlit naturally stacks these
        # on narrow screens.
        columns = st.columns(2)

        for index, (_, product) in enumerate(page_foods.iterrows()):
            with columns[index % 2]:

                product_id = int(product["Product ID"])
                brand = str(product["Brand"])
                product_name = str(product["Product"])
                retailer = str(product["Retailer"])
                package_size = str(product["Package Size"])
                serving_size = str(product["Serving Size"])
                image_url = str(product["Image URL"]).strip()

                with st.container(border=True):

                    # Compact product identity
                    if (
                        image_url
                        and image_url.lower() != "nan"
                        and image_url.startswith("http")
                    ):
                        image_html = f"""
                        <div class="product-thumb">
                            <img src="{image_url}">
                        </div>
                        """
                    else:
                        image_html = """
                        <div class="product-thumb">
                            <div class="product-thumb-placeholder">🛒</div>
                        </div>
                        """

                    st.html(
                        f"""
                        <div class="product-top">
                            {image_html}
                            <div class="product-copy">
                                <div class="brand">{brand}</div>
                                <div class="product-name">
                                    {product_name}
                                </div>
                                <div class="product-meta">
                                    {retailer} · {package_size}<br>
                                    Serving: {serving_size}
                                </div>
                            </div>
                        </div>
                        """
                    )

                    # Nutrients
                    nutrient_html = ""

                    for nutrient in targets:
                        nutrient_html += nutrient_bar_html(
                            nutrient,
                            float(product[nutrient]),
                            compact=True,
                        )

                    st.html(nutrient_html)

                    if st.button(
                        "＋ Add to basket",
                        key=f"add_{product_id}",
                        use_container_width=True,
                    ):
                        add_to_basket(
                            product_id,
                            product_name,
                        )

    # Pagination controls
    if total_pages > 1:
        st.divider()

        prev_col, page_col, next_col = st.columns([1, 1.2, 1])

        with prev_col:
            if st.button(
                "←",
                disabled=st.session_state.page <= 1,
                use_container_width=True,
            ):
                st.session_state.page -= 1
                st.rerun()

        with page_col:
            st.markdown(
                f"""
                <div style="text-align:center;padding-top:9px;
                            font-size:0.76rem;font-weight:700;color:#666D64;">
                    {st.session_state.page} / {total_pages}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with next_col:
            if st.button(
                "→",
                disabled=st.session_state.page >= total_pages,
                use_container_width=True,
            ):
                st.session_state.page += 1
                st.rerun()

# ---------------------------------------------------------
# FLOATING MOBILE BASKET
# ---------------------------------------------------------

nutrient_totals = calculate_totals()
total_servings = sum(st.session_state.basket.values())

mini_bars = ""

for nutrient in targets:
    percentage = (
        nutrient_totals[nutrient] / targets[nutrient]
    ) * 100

    display_percentage = min(max(percentage, 0), 100)
    colour = NUTRIENT_COLOURS[nutrient]

    mini_bars += f"""
        <div class="floating-track">
            <div class="floating-fill"
                 style="width:{display_percentage}%;background:{colour};">
            </div>
        </div>
    """

st.html(
    f"""
    <div class="floating-basket">
        <div class="floating-inner">
            <div class="floating-count">
                <strong>🛒 {total_servings} serves</strong>
                Basket
            </div>

            <div class="floating-bars">
                {mini_bars}
            </div>

            <div class="floating-arrow">
                Open →
            </div>
        </div>
    </div>
    """
)

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.caption(
    "Educational tool only. This calculator estimates nutrient "
    "contributions from selected foods and does not diagnose "
    "nutrient deficiencies or replace individual dietary advice "
    "from a qualified health professional."
)
