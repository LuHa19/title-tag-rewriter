import re
from urllib.parse import urlparse
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Luke's H1 & Title Tag Rewriter", page_icon="✍️", layout="wide"
)

st.title("Luke's H1 & Title Tag Rewriter Tool ✍️")
st.write(
    "Upload your crawl CSV to programmatically generate clean, unique H1s and"
    " Meta Titles based on rich URL taxonomy."
)


# --- 1. Cached File Loader ---
@st.cache_data(show_spinner="Loading CSV file into memory...")
def load_csv_data(uploaded_file):
    try:
        return pd.read_csv(uploaded_file, encoding="utf-8")
    except (UnicodeDecodeError, Exception):
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, encoding="latin1")


# --- Helper 1: Column Auto-Detection ---
def find_column(df, candidates):
    for col in df.columns:
        if col.strip().lower() in [c.lower() for c in candidates]:
            return col
    return None


# --- Helper 2: Word Deduplication ---
PROTECTED_WORDS = {
    "x",
    "w",
    "d",
    "h",
    "cm",
    "mm",
    "kg",
    "&",
    "and",
    "or",
    "in",
    "for",
    "of",
    "with",
    "|",
    "-",
}


def deduplicate_title_words(title_str):
    words = title_str.split()
    seen = set()
    clean_words = []
    for w in words:
        w_lower = re.sub(r"[\(\)\|,]", "", w.lower())
        if w_lower in PROTECTED_WORDS or w_lower not in seen:
            if w_lower not in PROTECTED_WORDS and len(w_lower) > 0:
                seen.add(w_lower)
            clean_words.append(w)
    return " ".join(clean_words)


# --- Helper 3: Rich Taxonomy Parser ---
BRANDS = [
    ("Rapid 1", ["rapid-1", "rapid 1"]),
    ("Rapid 2", ["rapid-2", "rapid 2"]),
    ("Probe", ["probe"]),
    ("QMP", ["qmp"]),
    ("Elite", ["elite"]),
    ("Pure", ["pure"]),
    ("Educate", ["educate"]),
    ("Value Line", ["value-line", "value line"]),
    ("Everyday", ["everyday"]),
    ("Titan", ["titan"]),
    ("Hille", ["hille"]),
    ("Bisley", ["bisley"]),
]

COLORS_MAP = [
    ("Blue/Grey", ["blue-grey", "blue/grey"]),
    ("Blue/Orange", ["blue-orange", "blue/orange"]),
    ("Blue", ["blue"]),
    ("Grey", ["grey", "gray"]),
    ("Red", ["red"]),
    ("Black", ["black"]),
    ("Green", ["green"]),
    ("White", ["white"]),
    ("Yellow", ["yellow"]),
    ("Silver", ["silver"]),
    ("Oak", ["oak"]),
    ("Beech", ["beech"]),
    ("Walnut", ["walnut"]),
    ("Maple", ["maple"]),
]

CATEGORY_PATTERNS = [
    ("Classroom Tables", ["classroom-tables", "classroom tables"]),
    ("Classroom Chairs", ["classroom-chairs", "classroom chairs"]),
    ("Office Desks", ["office-desks", "office desks", "desks-by-size", "desks"]),
    ("Executive Desks", ["executive-desks"]),
    ("Height Adjustable Desks", ["height-adjustable-desks"]),
    ("Office Chairs", ["office-chairs", "office chairs"]),
    ("Executive Chairs", ["executive-chairs"]),
    ("Door Lockers", ["door-lockers", "door lockers"]),
    ("Lockers", ["lockers"]),
    ("Shelving & Racking", ["shelving-racking"]),
    ("Shelving", ["shelving"]),
    ("Tables", ["tables"]),
    ("Chairs", ["chairs"]),
    ("Cupboards", ["cupboards"]),
    ("Pedestals", ["pedestals"]),
    ("Storage", ["storage"]),
]


def parse_url_taxonomy(url_str, curr_title="", curr_h1="", include_range=True):
    if not isinstance(url_str, str):
        return ""

    parsed = urlparse(url_str)
    filename = parsed.path.split("/")[-1]
    slug = re.sub(r"\.html$", "", filename).lower()
    full_path_str = parsed.path.lower()

    # A. Brand / Range
    brand_range = ""
    for b_name, b_kws in BRANDS:
        if any(kw in full_path_str for kw in b_kws):
            brand_range = b_name
            break

    # B. Duty / Grade Rating
    duty = ""
    if "heavy-duty" in slug or "heavy duty" in slug:
        duty = "Heavy Duty"
    elif "standard-shelving" in slug or "standard" in slug:
        duty = "Standard Duty"

    # C. Colour Detection
    colour = ""
    for c_name, c_kws in COLORS_MAP:
        if any(kw in slug for kw in c_kws):
            colour = c_name
            break

    # D. Shelves & Material Spec
    shelves_spec = ""
    shelves_match = re.search(
        r"with-(\d+)-(chipboard|melamine|wire-mesh|mesh|steel|wood)-shelves", slug
    )
    if shelves_match:
        count = shelves_match.group(1)
        mat = shelves_match.group(2).title().replace("-", " ")
        shelves_spec = f"With {count} {mat} Shelves"
    else:
        shelves_gen = re.search(
            r"(\d+)-(chipboard|melamine|mesh|steel)-shelves", slug
        )
        if shelves_gen:
            count = shelves_gen.group(1)
            mat = shelves_gen.group(2).title()
            shelves_spec = f"With {count} {mat} Shelves"

    # E. Door / Tier Spec
    spec_door, spec_tier = "", ""
    d_match = re.search(r"\b(\d+)\s*-?\s*door\b", slug)
    if d_match:
        spec_door = f"{d_match.group(1)} Door"

    t_match = re.search(r"\b(\d+)\s*-?\s*(tier|shelves)\b", slug)
    if t_match and not shelves_spec:
        spec_tier = f"{t_match.group(1)} Tier"

    # F. Dimensions & Capacity
    dimensions, capacity, age_group = "", "", ""
    dim_match = re.search(r"(\d+wx\d+h|\d+wx\d+dx\d+h)", slug)
    if dim_match:
        dimensions = dim_match.group(1)

    c_match = re.search(r"\b(\d+kg)\b", slug)
    if c_match:
        capacity = f"({c_match.group(1).upper()})"

    a_match = re.search(r"(\d+(?:-\d+)?(?:\+)?)-years?(?:-old)?", slug)
    if a_match:
        age_group = f"({a_match.group(1)} Years)"

    # G. Product Type Category
    product_type = ""
    for cat_name, keywords in CATEGORY_PATTERNS:
        if any(kw in full_path_str for kw in keywords):
            product_type = cat_name
            break

    # Construct in user's preferred order:
    # Range + Colour + Duty + Product Type + Shelves/Specs + Dimensions
    parts = []
    if include_range and brand_range:
        parts.append(brand_range)
    if colour:
        parts.append(colour)
    if duty:
        parts.append(duty)
    if spec_door:
        parts.append(spec_door)
    if spec_tier:
        parts.append(spec_tier)

    # Ensure product_type is present
    current_str = " ".join(parts)
    if product_type and product_type.lower() not in current_str.lower():
        parts.append(product_type)

    if shelves_spec:
        parts.append(shelves_spec)
    if dimensions:
        parts.append(dimensions)
    if age_group:
        parts.append(age_group)
    if capacity:
        parts.append(capacity)

    raw_h1 = " ".join(parts)
    return deduplicate_title_words(raw_h1)


# --- Helper 4: Safe Disambiguation Engine ---
def ensure_unique_title(url_str, base_h1, brand_suffix, max_len, seen_titles):
    def build_title(h1):
        raw = f"{h1}{brand_suffix}"
        if len(raw) <= max_len:
            return h1, raw
        max_body_len = max_len - len(brand_suffix)
        if max_body_len > 10:
            truncated = h1[:max_body_len].rsplit(" ", 1)[0]
            return truncated, f"{truncated}{brand_suffix}"
        else:
            return h1[:max_body_len], f"{h1[:max_body_len]}{brand_suffix}"

    h1_candidate, title_candidate = build_title(base_h1)

    if title_candidate not in seen_titles:
        seen_titles.add(title_candidate)
        return h1_candidate, title_candidate

    parsed = urlparse(url_str)
    segments = [
        s.replace("-", " ").title()
        for s in parsed.path.split("/")
        if s and not s.endswith(".html")
    ]

    for seg in reversed(segments[:-1]):
        diff_words = [
            w
            for w in seg.split()
            if w.lower() not in base_h1.lower()
            and w.lower()
            not in ["lockers", "tables", "desks", "chairs", "metric", "furniture"]
        ]
        if diff_words:
            diff_text = " ".join(diff_words)
            diff_h1 = deduplicate_title_words(f"{diff_text} {base_h1}")
            h1_cand, title_cand = build_title(diff_h1)

            if title_cand not in seen_titles:
                seen_titles.add(title_cand)
                return h1_cand, title_cand

    variant_counter = 2
    while True:
        tag = f" v{variant_counter}"
        max_body_len = max_len - len(brand_suffix) - len(tag)
        if max_body_len > 5:
            truncated_base = base_h1[:max_body_len].rsplit(" ", 1)[0]
            variant_h1 = f"{truncated_base}{tag}"
        else:
            variant_h1 = f"{base_h1[:max(1, max_body_len)]}{tag}"

        candidate_title = f"{variant_h1}{brand_suffix}"

        if candidate_title not in seen_titles:
            seen_titles.add(candidate_title)
            return variant_h1, candidate_title

        variant_counter += 1


# --- UI & Execution ---
uploaded_file = st.file_uploader("Upload CSV File", type=["csv", "tsv", "txt"])

if uploaded_file is not None:
    df = load_csv_data(uploaded_file)
    st.success(f"Successfully loaded {len(df):,} URLs!")

    default_url_col = find_column(
        df, ["Address", "URL", "Url", "Page Address", "Link"]
    )
    default_title_col = find_column(
        df,
        [
            "Title 1",
            "Title",
            "Meta Title 1",
            "Page Title",
            "Meta Title",
            "Title1",
        ],
    )
    default_h1_col = find_column(
        df, ["H1-1", "H1", "Heading 1", "H1-1 Title", "H1 1", "H11"]
    )

    st.subheader("📋 Select Column Mapping")
    col1, col2, col3 = st.columns(3)
    column_options = ["None"] + list(df.columns)

    with col1:
        url_col = st.selectbox(
            "URL / Address Column",
            df.columns,
            index=(
                df.columns.get_loc(default_url_col)
                if default_url_col in df.columns
                else 0
            ),
        )

    with col2:
        title_index = (
            df.columns.get_loc(default_title_col) + 1
            if default_title_col in df.columns
            else 0
        )
        title_col = st.selectbox(
            "Current Title Column", column_options, index=title_index
        )

    with col3:
        h1_index = (
            df.columns.get_loc(default_h1_col) + 1
            if default_h1_col in df.columns
            else 0
        )
        h1_col = st.selectbox(
            "Current H1 Column", column_options, index=h1_index
        )

    # Increased default character limit to 90 so descriptive titles fit cleanly
    max_title_len = st.number_input(
        "Max Title Tag Length (Characters)",
        min_value=30,
        max_value=120,
        value=90,
    )

    if st.button("Generate Rewritten Titles & H1s"):
        with st.spinner("Processing titles..."):
            results = []
            seen_recommended_titles = set()
            brand_suffix = " | Furniture At Work"
            total_rows = len(df)

            progress_bar = st.progress(0.0)
            status_text = st.empty()

            for index, row in df.iterrows():
                if (index % 100 == 0) or (index == total_rows - 1):
                    progress_val = min(1.0, (index + 1) / total_rows)
                    status_text.text(
                        f"Processing row {index + 1:,} of {total_rows:,}..."
                    )
                    progress_bar.progress(progress_val)

                url = str(row[url_col])
                current_title = (
                    str(row[title_col])
                    if (title_col != "None" and title_col in df.columns)
                    else ""
                )
                current_h1 = (
                    str(row[h1_col])
                    if (h1_col != "None" and h1_col in df.columns)
                    else ""
                )

                raw_h1 = parse_url_taxonomy(
                    url,
                    curr_title=current_title,
                    curr_h1=current_h1,
                    include_range=False,
                )
                final_h1, final_title = ensure_unique_title(
                    url,
                    raw_h1,
                    brand_suffix,
                    max_title_len,
                    seen_recommended_titles,
                )

                results.append({
                    "URL / Address": url,
                    "Current Title Tag": current_title,
                    "Recommended Title Tag": final_title,
                    "Current H1": current_h1,
                    "Recommended H1": final_h1,
                    "Title Tag Length": len(final_title),
                })

            status_text.empty()
            progress_bar.empty()

        output_df = pd.DataFrame(results)
        st.subheader("🎉 Generated Optimization Table")
        st.dataframe(output_df)

        csv_data = output_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Rewritten Titles & H1s CSV",
            data=csv_data,
            file_name="rewritten_titles_and_h1s.csv",
            mime="text/csv",
        )
