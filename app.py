import streamlit as st
import pandas as pd
from rapidfuzz import fuzz

# ---------------------------------------------------------
# PAGE SETUP
# ---------------------------------------------------------

st.set_page_config(
    page_title="Plant-Based Grocery Basket",
    page_icon="🌱",
    layout="wide"
)

# ---------------------------------------------------------
# COLOURS
# ---------------------------------------------------------

NUTRIENT_COLOURS = {
    "IRON (mg)": "#D1007A",
    "IODINE (µg)": "#8FD3FF",
    "B12 (µg)": "#4CAF50",
    "CALCIUM (mg)": "#F4D35E",
    "OMEGA3 ALA (mg)": "#C47A32"
}

NUTRIENT_NAMES = {
    "IRON (mg)": "Iron",
    "B12 (µg)": "Vitamin B12",
    "IODINE (µg)": "Iodine",
    "CALCIUM (mg)": "Calcium",
    "OMEGA3 ALA (mg)": "Omega-3 ALA"
}

NUTRIENT_ICONS = {
    "IRON (mg)": "🩸",
    "B12 (µg)": "🌱",
    "IODINE (µg)": "💧",
    "CALCIUM (mg)": "🦴",
    "OMEGA3 ALA (mg)": "🫒"
}

# Daily reference targets used for the demonstration MVP
targets = {
    "IRON (mg)": 18,
    "B12 (µg)": 2.4,
    "IODINE (µg)": 150,
    "CALCIUM (mg)": 1000,
    "OMEGA3 ALA (mg)": 1100
}

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

foods = pd.read_csv("foods.csv")

foods["Product ID"] = foods.index

# ---------------------------------------------------------
# HANDLE OMEGA-3 COLUMN
# ---------------------------------------------------------

# Support either the old or new CSV column name.
if "OMEGA3 ALA (mg)" not in foods.columns:

    if "OMEGA3 (mg)" in foods.columns:

        foods["OMEGA3 ALA (mg)"] = foods["OMEGA3 (mg)"]

    else:

        foods["OMEGA3 ALA (mg)"] = 0

# ---------------------------------------------------------
# NUTRIENT COLUMNS
# ---------------------------------------------------------

for nutrient in targets:

    foods[nutrient] = pd.to_numeric(
        foods[nutrient],
        errors="coerce"
    ).fillna(0)

# ---------------------------------------------------------
# IMAGE URL
# ---------------------------------------------------------

if "Image URL" not in foods.columns:
    foods["Image URL"] = ""

foods["Image URL"] = (
    foods["Image URL"]
    .fillna("")
    .astype(str)
)
# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "basket" not in st.session_state:
    st.session_state.basket = {}

if "nutrient_focus" not in st.session_state:
    st.session_state.nutrient_focus = None

if "show_basket" not in st.session_state:
    st.session_state.show_basket = False

if "page" not in st.session_state:
    st.session_state.page = 1

# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------

st.markdown(
    """
    <style>

    /* Main page */

   .main {
    padding-top: 1rem;
    padding-bottom: 9rem;
    }

    h1 {
        letter-spacing: -0.5px;
    }

    /* Product card */

    .product-card {
        border: 1px solid #E6E6E6;
        border-radius: 18px;
        padding: 0;
        background: white;
        overflow: hidden;
        margin-bottom: 1rem;
        box-shadow: 0 3px 12px rgba(0,0,0,0.05);
        height: 100%;
    }

    .product-image {
        width: 100%;
        height: 210px;
        background: #F7F7F7;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }

    .product-image img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        background: white;
    }

    .image-placeholder {
        text-align: center;
        color: #A0A0A0;
        font-size: 42px;
    }

    .product-content {
        padding: 18px;
    }

    .brand {
        font-size: 0.82rem;
        font-weight: 700;
        color: #777777;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-bottom: 3px;
    }

    .product-name {
        font-size: 1.15rem;
        font-weight: 700;
        line-height: 1.25;
        margin-bottom: 10px;
    }

    .product-meta {
        font-size: 0.82rem;
        color: #666666;
        line-height: 1.5;
        margin-bottom: 14px;
    }

    /* Nutrient bars */

    .nutrient-row {
        margin-bottom: 10px;
    }

    .nutrient-label {
        font-size: 0.78rem;
        font-weight: 600;
        margin-bottom: 4px;
    }

    .nutrient-bar-background {
        width: 100%;
        height: 8px;
        background: #EEEEEE;
        border-radius: 20px;
        overflow: hidden;
    }

    .nutrient-bar {
        height: 8px;
        border-radius: 20px;
    }

    .nutrient-percent {
        font-size: 0.72rem;
        color: #777777;
        margin-top: 3px;
    }

    /* Basket summary */

    .basket-summary {
        border-radius: 16px;
        background: #F8F8F8;
        padding: 16px;
        margin-top: 10px;
        margin-bottom: 15px;
    }

    .basket-product {
        border-bottom: 1px solid #E5E5E5;
        padding: 10px 0;
    }

    /* Mobile */

    @media (max-width: 768px) {

        .main {
            padding-left: 0.6rem;
            padding-right: 0.6rem;
            padding-bottom: 8rem;
        }

        .product-image {
            height: 190px;
        }

        .product-content {
            padding: 16px;
        }

        .product-name {
            font-size: 1.08rem;
        }

        .nutrient-label {
            font-size: 0.76rem;
        }

        .nutrient-percent {
            font-size: 0.7rem;
        }

        div.stButton > button {
            min-height: 46px;
            border-radius: 12px;
            font-weight: 600;
        }
    }

    /* Bottom basket bar */

    .sticky-basket {
        position: fixed;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 999999;
        background: rgba(255,255,255,0.97);
        backdrop-filter: blur(10px);
        border-top: 1px solid #DDDDDD;
        padding: 10px 18px 12px 18px;
        box-shadow: 0 -4px 20px rgba(0,0,0,0.08);
    }

    .sticky-inner {
        max-width: 1200px;
        margin: auto;
    }

    .sticky-title {
        font-size: 0.8rem;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .mini-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 8px;
    }

    .mini-label {
        font-size: 0.68rem;
        margin-bottom: 3px;
    }

    .mini-background {
        height: 5px;
        background: #E8E8E8;
        border-radius: 10px;
        overflow: hidden;
    }

    .mini-bar {
        height: 5px;
        border-radius: 10px;
    }

    .basket-link {
        display: block;
        text-align: center;
        margin-top: 8px;
        padding: 8px;
        background: #111111;
        color: white !important;
        text-decoration: none;
        border-radius: 10px;
        font-weight: 700;
        font-size: 0.82rem;
    }

    @media (max-width: 768px) {

        .sticky-basket {
            padding: 8px 10px 10px 10px;
        }

        .mini-grid {
            gap: 5px;
        }

        .mini-label {
            font-size: 0.58rem;
        }

        .basket-link {
            margin-top: 6px;
            padding: 9px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("🌱 Plant-Based Grocery Basket")

st.write(
    "Build a grocery basket and see how your selected foods "
    "contribute to key nutrients."
)

# ---------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------

with st.sidebar:

    st.header("🔎 Find food")

    search = st.text_input(
        "Search products",
        placeholder="Try tofu, oats, Weet-Bix..."
    )

    retailers = ["All"] + sorted(
        foods["Retailer"].dropna().unique().tolist()
    )

    retailer_filter = st.selectbox(
        "Retailer",
        retailers
    )

    categories = ["All"] + sorted(
        foods["Category"].dropna().unique().tolist()
    )

    category_filter = st.selectbox(
        "Category",
        categories
    )

    vegan_only = st.checkbox(
        "🌱 Vegan products only"
    )

    st.divider()

    st.subheader("🛒 Basket")

    total_servings = sum(
        st.session_state.basket.values()
    )

    st.metric(
        "Selected servings",
        total_servings
    )

    if st.button(
        "Clear basket",
        use_container_width=True
    ):
        st.session_state.basket = {}
        st.rerun()

# ---------------------------------------------------------
# SEARCH / FILTER
# ---------------------------------------------------------

filtered_foods = foods.copy()

if search:

    search_clean = search.lower().strip()

    def fuzzy_match(product):

        product_clean = product.lower()

        if search_clean in product_clean:
            return True

        words = product_clean.replace("-", " ").split()

        for word in words:
            if fuzz.ratio(search_clean, word) >= 55:
                return True

        return fuzz.partial_ratio(
            search_clean,
            product_clean
        ) >= 55

    filtered_foods = filtered_foods[
        filtered_foods["Product"].astype(str).apply(
            fuzzy_match
        )
    ]

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

# ---------------------------------------------------------
# SORTING
# ---------------------------------------------------------
# ---------------------------------------------------------
# CATEGORY RIBBON
# ---------------------------------------------------------

st.markdown(
    """
    <style>

    .category-ribbon {
        display: flex;
        gap: 8px;
        overflow-x: auto;
        padding: 4px 0 12px 0;
        margin-bottom: 8px;
        scrollbar-width: none;
    }

    .category-ribbon::-webkit-scrollbar {
        display: none;
    }

    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    "### Browse by category"
)

category_options = [
    "All",
    "Dairy",
    "Pantry",
    "Vegetables",
    "Grains",
    "Legumes",
    "Nuts & Seeds",
    "Snacks"
]

# Store selected category
if "ribbon_category" not in st.session_state:
    st.session_state.ribbon_category = "All"

category_cols = st.columns(
    len(category_options)
)

for i, category in enumerate(category_options):

    with category_cols[i]:

        if st.button(
            category,
            key=f"category_{category}",
            use_container_width=True
        ):

            st.session_state.ribbon_category = category
            st.session_state.page = 1
            st.rerun()

st.subheader("🛍️ Grocery catalogue")

sort_options = {
    "Default": None,
    "Iron — highest first": "IRON (mg)",
    "Vitamin B12 — highest first": "B12 (µg)",
    "Iodine — highest first": "IODINE (µg)",
    "Calcium — highest first": "CALCIUM (mg)",
    "Omega-3 ALA — highest first": "OMEGA3 ALA (mg)",
    "Product name — A–Z": "Product"
}

sort_choice = st.selectbox(
    "Sort by",
    list(sort_options.keys()),
    label_visibility="collapsed"
)

sort_column = sort_options[sort_choice]

if sort_column:

    if sort_column == "Product":

        filtered_foods = filtered_foods.sort_values(
            by="Product",
            ascending=True,
            na_position="last"
        )

    else:

        filtered_foods = filtered_foods.sort_values(
            by=sort_column,
            ascending=False,
            na_position="last"
        )
if st.session_state.ribbon_category != "All":

    filtered_foods = filtered_foods[
        filtered_foods["Category"]
        .astype(str)
        .str.strip()
        .str.lower()
        ==
        st.session_state.ribbon_category
        .lower()
    ]
# ---------------------------------------------------------
# NUTRIENT RECOMMENDATION
# ---------------------------------------------------------

if st.session_state.nutrient_focus:

    nutrient = st.session_state.nutrient_focus

    st.info(
        f"Showing foods that are among the stronger sources of "
        f"{NUTRIENT_NAMES[nutrient]}."
    )

    positive_foods = filtered_foods[
        filtered_foods[nutrient] > 0
    ]

    if len(positive_foods) > 0:

        threshold = positive_foods[nutrient].median()

        filtered_foods = positive_foods[
            positive_foods[nutrient] >= threshold
        ]

        filtered_foods = filtered_foods.sort_values(
            nutrient,
            ascending=False
        )

# ---------------------------------------------------------
# PAGINATION
# ---------------------------------------------------------

PRODUCTS_PER_PAGE = 12

total_pages = max(
    1,
    (len(filtered_foods) + PRODUCTS_PER_PAGE - 1)
    // PRODUCTS_PER_PAGE
)

if st.session_state.page > total_pages:
    st.session_state.page = total_pages

start = (
    st.session_state.page - 1
) * PRODUCTS_PER_PAGE

end = start + PRODUCTS_PER_PAGE

page_foods = filtered_foods.iloc[start:end]
# ---------------------------------------------------------
# PRODUCT CARDS
# ---------------------------------------------------------

if len(page_foods) == 0:

    st.warning(
        "No products found. Try changing your search or filters."
    )

else:

    columns = st.columns(2)

    for index, (_, product) in enumerate(page_foods.iterrows()):

        col = columns[index % 2]

        with col:

            # Reliable Streamlit container for the whole product
            with st.container(border=True):

                product_id = int(product["Product ID"])

                brand = str(product["Brand"])
                product_name = str(product["Product"])
                retailer = str(product["Retailer"])
                package_size = str(product["Package Size"])
                serving_size = str(product["Serving Size"])

                image_url = str(product["Image URL"]).strip()

                # -------------------------------------------------
                # PRODUCT IMAGE
                # -------------------------------------------------

                if (
                    image_url
                    and image_url.lower() != "nan"
                    and image_url.startswith("http")
                ):

                    st.html(
                        f"""
                        <div class="product-image">
                            <img src="{image_url}">
                        </div>
                        """
                    )

                else:

                    st.html(
                        """
                        <div class="product-image">
                            <div class="image-placeholder">
                                🛒
                            </div>
                        </div>
                        """
                    )

                # -------------------------------------------------
                # PRODUCT INFORMATION
                # -------------------------------------------------

                st.html(
                    f"""
                    <div class="product-content">

                        <div class="brand">
                            {brand}
                        </div>

                        <div class="product-name">
                            {product_name}
                        </div>

                        <div class="product-meta">
                            🏪 {retailer}<br>
                            📦 {package_size}<br>
                            🍽️ Serving: {serving_size}
                        </div>

                    </div>
                    """
                )

                # -------------------------------------------------
                # NUTRIENT BARS
                # -------------------------------------------------

                for nutrient in targets:

                    value = float(product[nutrient])
                    target = targets[nutrient]

                    percentage = (value / target) * 100

                    display_percentage = min(
                        percentage,
                        100
                    )

                    colour = NUTRIENT_COLOURS[nutrient]
                    name = NUTRIENT_NAMES[nutrient]
                    icon = NUTRIENT_ICONS[nutrient]

                    unit = (
                        "mg"
                        if "(mg)" in nutrient
                        else "µg"
                    )

                    st.html(
                        f"""
                        <div class="nutrient-row">

                            <div class="nutrient-label">
                                {icon} {name}
                            </div>

                            <div class="nutrient-bar-background">

                                <div
                                    class="nutrient-bar"
                                    style="
                                        width:{display_percentage}%;
                                        background:{colour};
                                    "
                                ></div>

                            </div>

                            <div class="nutrient-percent">
                                {value:.1f} {unit}
                                / {percentage:.0f}%
                                of reference target
                            </div>

                        </div>
                        """
                    )

                # -------------------------------------------------
                # ADD TO BASKET
                # -------------------------------------------------

                if st.button(
                    "＋ Add to basket",
                    key=f"add_{product_id}",
                    use_container_width=True
                ):

                    if product_id in st.session_state.basket:

                        st.session_state.basket[
                            product_id
                        ] += 1

                    else:

                        st.session_state.basket[
                            product_id
                        ] = 1

                    st.toast(
                        f"{product_name} added to basket!"
                    )

                    st.rerun()

# ---------------------------------------------------------
# PAGINATION
# ---------------------------------------------------------

if total_pages > 1:

    st.divider()

    page_col1, page_col2, page_col3 = st.columns(
        [1, 2, 1]
    )

    with page_col1:

        if st.button(
            "← Previous",
            disabled=st.session_state.page <= 1,
            use_container_width=True
        ):

            st.session_state.page -= 1
            st.rerun()

    with page_col2:

        st.markdown(
            f"""
            <div style="
                text-align:center;
                padding-top:8px;
                font-weight:600;
            ">
                Page {st.session_state.page}
                of {total_pages}
            </div>
            """,
            unsafe_allow_html=True
        )

    with page_col3:

        if st.button(
            "Next →",
            disabled=st.session_state.page >= total_pages,
            use_container_width=True
        ):

            st.session_state.page += 1
            st.rerun()

# ---------------------------------------------------------
# BASKET CALCULATIONS
# ---------------------------------------------------------

nutrient_totals = {
    nutrient: 0
    for nutrient in targets
}

for product_id, servings in st.session_state.basket.items():

    product_matches = foods[
        foods["Product ID"] == product_id
    ]

    if len(product_matches) == 0:
        continue

    product = product_matches.iloc[0]

    for nutrient in targets:

        value = pd.to_numeric(
            product[nutrient],
            errors="coerce"
        )

        if pd.notna(value):

            nutrient_totals[nutrient] += (
                value * servings
            )

# ---------------------------------------------------------
# BASKET OVERVIEW ANCHOR
# ---------------------------------------------------------

st.markdown(
    '<div id="basket-overview"></div>',
    unsafe_allow_html=True
)

st.divider()

st.header("🛒 Basket overview")

if not st.session_state.basket:

    st.info(
        "Your basket is empty. Add some foods from the catalogue above."
    )

else:

    # -----------------------------------------------------
    # BASKET PRODUCTS
    # -----------------------------------------------------

    for product_id, servings in list(
        st.session_state.basket.items()
    ):

        product = foods[
            foods["Product ID"] == product_id
        ].iloc[0]

        product_name = product["Product"]

        basket_col1, basket_col2, basket_col3 = st.columns(
            [5, 2, 1]
        )

        with basket_col1:

            st.markdown(
                f"""
                <div class="basket-product">
                    <strong>{product["Brand"]}</strong><br>
                    {product_name}<br>
                    <small>
                        {product["Retailer"]} ·
                        {product["Serving Size"]}
                    </small>
                </div>
                """,
                unsafe_allow_html=True
            )

        with basket_col2:

            new_servings = st.number_input(
                "Servings",
                min_value=1,
                max_value=99,
                value=int(servings),
                step=1,
                key=f"servings_{product_id}"
            )

            if new_servings != servings:

                st.session_state.basket[
                    product_id
                ] = new_servings

                st.rerun()

        with basket_col3:

            st.write("")

            if st.button(
                "Remove",
                key=f"remove_{product_id}"
            ):

                del st.session_state.basket[
                    product_id
                ]

                st.rerun()

    # -----------------------------------------------------
    # TOTAL NUTRIENT DASHBOARD
    # -----------------------------------------------------

    st.subheader("Your basket provides")

    for nutrient in targets:

        total = nutrient_totals[nutrient]
        target = targets[nutrient]

        percentage = (
            total / target
        ) * 100

        display_percentage = min(
            percentage,
            100
        )

        colour = NUTRIENT_COLOURS[nutrient]
        name = NUTRIENT_NAMES[nutrient]
        icon = NUTRIENT_ICONS[nutrient]

        unit = (
            "mg"
            if "(mg)" in nutrient
            else "µg"
        )

    st.html(
    f"""
    <div style="margin-bottom:16px;">

        <div style="
            display:flex;
            justify-content:space-between;
            font-weight:600;
            margin-bottom:5px;
        ">
            <span>{icon} {name}</span>
            <span>{percentage:.0f}%</span>
        </div>

        <div style="
            width:100%;
            height:14px;
            background:#EAEAEA;
            border-radius:20px;
            overflow:hidden;
        ">

            <div style="
                width:{display_percentage}%;
                height:14px;
                background:{colour};
                border-radius:20px;
            "></div>

        </div>

        <div style="
            font-size:0.78rem;
            color:#777;
            margin-top:4px;
        ">
            {total:.1f} {unit}
            / {target} {unit} reference target
        </div>

    </div>
    """
    )   

    # -----------------------------------------------------
    # LOWEST NUTRIENT INSIGHT
    # -----------------------------------------------------

    coverage = {
        nutrient:
        nutrient_totals[nutrient] / targets[nutrient]
        for nutrient in targets
        }

    lowest_nutrient = min(
        coverage,
        key=coverage.get
    )

    lowest_percentage = (
        coverage[lowest_nutrient] * 100
    )

    st.info(
        f"💡 Your lowest-covered nutrient is "
        f"**{NUTRIENT_NAMES[lowest_nutrient]}** "
        f"at approximately {lowest_percentage:.0f}% "
        f"of the reference target."
    )

    if st.button(
        f"Find foods high in {NUTRIENT_NAMES[lowest_nutrient]}",
        use_container_width=True
    ):

        st.session_state.nutrient_focus = (
            lowest_nutrient
        )

        st.session_state.page = 1

        st.rerun()

    if st.button(
        "Clear basket",
        use_container_width=True
    ):

        st.session_state.basket = {}

        st.rerun()

## ---------------------------------------------------------
# FIXED BOTTOM BASKET BAR
# ---------------------------------------------------------

mini_bars = ""

for nutrient in targets:

    total = nutrient_totals[nutrient]
    target = targets[nutrient]

    percentage = (total / target) * 100
    display_percentage = min(percentage, 100)

    colour = NUTRIENT_COLOURS[nutrient]
    name = NUTRIENT_NAMES[nutrient]

    mini_bars += f"""
        <div>
            <div class="mini-label">
                {name} {percentage:.0f}%
            </div>

            <div class="mini-background">
                <div
                    class="mini-bar"
                    style="
                        width:{display_percentage}%;
                        background:{colour};
                    "
                ></div>
            </div>
        </div>
    """

st.html(
    f"""
    <div class="sticky-basket">

        <div class="sticky-inner">

            <div class="sticky-title">
                🛒 Your basket · {total_servings} servings
            </div>

            <div class="mini-grid">
                {mini_bars}
            </div>

            <a
                href="#basket-overview"
                class="basket-link"
            >
                View basket ↑
            </a>

        </div>

    </div>
    """
)# ---------------------------------------------------------
# DISCLAIMER
# ---------------------------------------------------------

st.caption(
    "Educational tool only. This calculator estimates nutrient "
    "contributions from selected foods and does not diagnose "
    "nutrient deficiencies or replace individual dietary advice "
    "from a qualified health professional."
)