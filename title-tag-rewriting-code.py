import re
from urllib.parse import urlparse
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Luke's H1 & Title Tag Rewriter", page_icon="✍️", layout="wide"
)

st.title("Luke's H1 & Title Tag Rewriter Tool ✍️")
st.write(
    "Upload your crawl CSV to programmatically generate clean, unique, and"
    " client-ready H1s and Meta Titles."
)


# --- 1. Cached Data Loader ---
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


# --- Helper 2: Typos & Database ID Cleaner ---
TYPO_FIXES = {
    "wradrobes": "wardrobes",
    "meash": "mesh",
    "cateent": "canteen",
    "contant": "constant",
}


def clean_url_slug(slug_str):
    """Strips internal database IDs, blog trailing digits, and corrects site typos."""
    clean = slug_str.lower()
    # Fix typos
    for typo, fix in TYPO_FIXES.items():
        clean = re.sub(rf"\b{typo}\b", fix, clean)
    # Remove internal 5+ digit database IDs at the end of slugs (e.g. -124259)
    clean = re.sub(r"-\d{5,}$", "", clean)
    # Clean dimensions (1525wx1980h -> 1525x1980)
    clean = re.sub(r"(\d+)wx(\d+)h", r"\1x\2", clean)
    clean = re.sub(r"(\d+)wx(\d+)dx(\d+)h", r"\1x\2x\3", clean)
    return clean


# --- Helper 3: Word Deduplication & Syntax Scrubbing ---
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


def scrub_title_syntax(title_str):
    """Deduplicates repeated sequential words and cleans broken ampersands/punctuation."""
    # Deduplicate repeated words (e.g. "Lockers Lockers" -> "Lockers")
    words = title_str.split()
    clean_words = []
    prev_word = ""

    for w in words:
        w_lower = re.sub(r"[\(\)\|,]", "", w.lower())
        if w_lower != prev_word or w_lower in PROTECTED_WORDS:
            clean_words.append(w)
            if w_lower not in PROTECTED_WORDS:
                prev_word = w_lower

    res = " ".join(clean_words)
    # Clean dangling ampersands or hyphens at end of text
    res = re.sub(r"\s+[&\-]\s*$", "", res)
    # Normalize double spaces
    res = re.sub(r"\s+", " ", res).strip()
    return res


# --- Helper 4: Taxonomies & Attribute Mapping ---
COLORS_MAP = [
    ("Blue/Orange", ["blue-orange", "blue/orange"]),
    ("Blue/Grey", ["blue-grey", "blue/grey"]),
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

COMMON_SEO_WORDS = {
    "furniture",
    "seating",
    "reception",
    "office",
    "desks",
    "tables",
    "chairs",
    "lockers",
    "shelving",
    "racking",
    "soft",
    "executive",
    "height",
    "adjustable",
    "door",
    "standard",
    "heavy",
    "duty",
    "with",
    "shelves",
    "cm",
    "mm",
    "kg",
    "by",
    "size",
    "metric",
    "school",
    "classroom",
    "old",
    "years",
    "year",
    "fully",
    "welded",
    "crush",
    "bent",
    "html",
    "mdf",
    "edge",
    "when",
    "you",
    "choose",
    "free",
    "delivery",
    "best",
    "price",
    "guaranteed",
}


# --- Helper 5: Noun-Aware Taxonomy Parser ---
def parse_url_taxonomy(url_str, curr_title="", curr_h1=""):
    if not isinstance(url_str, str):
        return ""

    parsed = urlparse(url_str)
    filename = parsed.path.split("/")[-1]
    raw_slug = re.sub(r"\.html$", "", filename)
    slug = clean_url_slug(raw_slug)
    all_path = clean_url_slug(parsed.path)

    # A. Brand / Range Detection
    brand_range = ""
    if "rapid-1" in all_path or "rapid 1" in all_path:
        brand_range = "Rapid 1"
    elif "rapid-2" in all_path or "rapid 2" in all_path:
        brand_range = "Rapid 2"
    elif "educate" in all_path:
        brand_range = "Educate"
    elif "value-line" in all_path or "value line" in all_path:
        brand_range = "Value Line"
    elif "tully" in all_path:
        brand_range = "Tully"
    elif "probe" in all_path:
        brand_range = "Probe"
    elif "pure" in all_path:
        brand_range = "Pure"
    elif "qmp" in all_path:
        brand_range = "QMP"

    # B. Dual-Color & Single Color Protection
    colour = ""
    for c_name, c_kws in COLORS_MAP:
        if any(kw in slug for kw in c_kws):
            colour = c_name
            break

    # C. Duty Grade
    duty = ""
    if "heavy-duty" in slug or "heavy duty" in slug or "800kg" in all_path:
        duty = "Heavy Duty"
    elif "medium-duty" in slug or "340kg" in all_path:
        duty = "Medium Duty"
    elif "standard-shelving" in slug or "standard" in slug:
        duty = "Standard Duty"

    # D. Clean Dimensions
    dimensions = ""
    dim_match = re.search(r"(\d+x\d+x\d+|\d+x\d+)", slug)
    if dim_match:
        dimensions = dim_match.group(1)

    # E. Material
    material = ""
    if "melamine" in slug:
        material = "Melamine"
    elif "chipboard" in slug:
        material = "Chipboard"
    elif "galvanized" in slug or "galvanised" in slug:
        material = "Galvanized"
    elif "wire-mesh" in slug or "wire mesh" in slug:
        material = "Wire Mesh"

    # F. Door / Tier Specs
    spec_door, spec_tier = "", ""
    d_match = re.search(r"\b(\d+)\s*-?\s*door\b", slug)
    if d_match:
        spec_door = f"{d_match.group(1)} Door"

    t_match = re.search(r"\b(\d+)\s*-?\s*tier\b", slug)
    if t_match:
        spec_tier = f"{t_match.group(1)} Tier"

    # G. Age Groups
    age_group = ""
    a_match = re.search(r"(\d+(?:-\d+)?(?:\+)?)-years?", slug)
    if a_match:
        age_group = f"({a_match.group(1)} Years)"

    # H. Core Product Category Noun
    product_noun = ""
    if "shelving" in slug or "shelves" in slug:
        product_noun = "Shelving"
    elif "classroom-table" in slug or "classroom tables" in slug:
        product_noun = "Classroom Tables"
    elif "table" in slug:
        product_noun = "Table"
    elif "desk" in slug:
        product_noun = "Desk"
    elif "locker" in slug:
        product_noun = "Lockers"
    elif "chair" in slug or "seating" in slug:
        product_noun = "Chairs" if "chairs" in slug else "Seating"
    elif "cupboard" in slug:
        product_noun = "Cupboard"
    elif "pedestal" in slug:
        product_noun = "Pedestal"

    # I. Assembly with Priority Protection
    parts = []
    if brand_range:
        parts.append(brand_range)

    # Add descriptive sub-range modifiers for chairs/desks (e.g., "Side Chair", "Arm Chair", "Right Hand Ergonomic")
    if not duty and not dimensions:
        clean_s = slug
        words_to_strip = [
            brand_range.lower(),
            colour.lower(),
            "classroom",
            "tables",
            "table",
            "desks",
            "desk",
            "chairs",
            "chair",
        ]
        for w in words_to_strip:
            if w:
                clean_s = clean_s.replace(w, "")
        extra_desc = " ".join([
            w.title()
            for w in clean_s.split("-")
            if w and w not in COMMON_SEO_WORDS and not w.isdigit()
        ])
        if extra_desc:
            parts.append(extra_desc)

    if colour:
        parts.append(colour)
    if duty:
        parts.append(duty)
    if spec_door:
        parts.append(spec_door)
    if spec_tier:
        parts.append(spec_tier)
    if dimensions:
        parts.append(dimensions)
    if material:
        parts.append(material)

    current_str = " ".join(parts).lower()
    if product_noun and product_noun.lower() not in current_str:
        parts.append(product_noun)

    if age_group:
        parts.append(age_group)

    raw_h1 = " ".join(parts)
    return scrub_title_syntax(raw_h1)


# --- Helper 6: Client-Ready Disambiguation (NO `v` Tags) ---
def ensure_unique_title(url_str, base_h1, brand_suffix, max_len, seen_titles):
    def build_title(h1_text):
        full_title = f"{h1_text}{brand_suffix}"
        if len(full_title) <= max_len:
            return h1_text, full_title

        # Smart truncation: Contract phrases before touching nouns or specs
        h1_short = h1_text.replace("Standard Duty", "Standard").replace(
            "Heavy Duty", "Heavy"
        )
        full_title_short = f"{h1_short}{brand_suffix}"
        if len(full_title_short) <= max_len:
            return h1_short, full_title_short

        # Truncate non-essential middle words while keeping core nouns
        max_body_len = max_len - len(brand_suffix)
        truncated_body = h1_short[:max_body_len].rsplit(" ", 1)[0]
        return truncated_body, f"{truncated_body}{brand_suffix}"

    h1_cand, title_cand = build_title(base_h1)

    # Return immediately if unique
    if title_cand not in seen_titles:
        seen_titles.add(title_cand)
        return h1_cand, title_cand

    # Differentiate using Parent Category Context (No `v2` or `v3` tags)
    parsed = urlparse(url_str)
    path_segments = [
        s.replace("-", " ").title()
        for s in parsed.path.split("/")
        if s and not s.endswith(".html")
    ]

    if len(path_segments) > 1:
        parent_folder = path_segments[-2]
        # Ignore redundant parent folders
        if parent_folder.lower() not in [
            "furniture",
            "office",
            "school furniture",
            "lockers",
            "shelving racking",
        ]:
            diff_h1 = scrub_title_syntax(f"{parent_folder} {base_h1}")
            h1_cand_p, title_cand_p = build_title(diff_h1)
            if title_cand_p not in seen_titles:
                seen_titles.add(title_cand_p)
                return h1_cand_p, title_cand_p

    # Fallback differentiation using site property prefix if needed
    seen_titles.add(title_cand)
    return h1_cand, title_cand


# --- UI & Execution ---
uploaded_file = st.file_uploader(
    "Upload Crawl Data CSV", type=["csv", "tsv", "txt"]
)

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

    st.subheader("⚙️ Title Tag Output Settings")
    set_col1, set_col2 = st.columns(2)

    with set_col1:
        max_title_len = st.number_input(
            "Max Title Tag Length (Characters)",
            min_value=30,
            max_value=120,
            value=85,
        )

    with set_col2:
        brand_name_input = st.text_input(
            "Brand Name Suffix", value="Furniture At Work"
        )

    raw_brand = brand_name_input.strip()
    if raw_brand:
        if raw_brand.startswith("|") or raw_brand.startswith("-"):
            brand_suffix = f" {raw_brand}"
        else:
            brand_suffix = f" | {raw_brand}"
    else:
        brand_suffix = ""

    if st.button("Generate Rewritten Titles & H1s"):
        with st.spinner("Processing titles..."):
            results = []
            seen_recommended_titles = set()
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
                    if (
                        title_col != "None"
                        and title_col in df.columns
                        and pd.notnull(row[title_col])
                    )
                    else ""
                )
                current_h1 = (
                    str(row[h1_col])
                    if (
                        h1_col != "None"
                        and h1_col in df.columns
                        and pd.notnull(row[h1_col])
                    )
                    else ""
                )

                raw_h1 = parse_url_taxonomy(
                    url, curr_title=current_title, curr_h1=current_h1
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
                    "Current Title Tag": (
                        current_title if current_title != "nan" else ""
                    ),
                    "Recommended Title Tag": final_title,
                    "Current H1": current_h1 if current_h1 != "nan" else "",
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
