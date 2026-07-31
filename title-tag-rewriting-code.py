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
    " Meta Titles based on dynamic URL taxonomy, search volumes, and keyword"
    " weighting."
)


# --- 1. Cached Data Loaders ---
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


# --- Helper 3: Structural SEO Taxonomies ---
CATEGORY_PATTERNS = [
    ("Classroom Tables", ["classroom-tables", "classroom tables"]),
    ("Classroom Chairs", ["classroom-chairs", "classroom chairs"]),
    ("Executive Desks", ["executive-desks", "executive desks"]),
    ("Height Adjustable Desks", ["height-adjustable-desks"]),
    ("Reception Desks", ["reception-desks", "reception desks"]),
    ("Soft Seating", ["soft-seating", "soft seating"]),
    ("Reception Furniture", ["reception-furniture", "reception furniture"]),
    ("Office Desks", ["office-desks", "office desks", "desks-by-size"]),
    ("Executive Chairs", ["executive-chairs"]),
    ("Office Chairs", ["office-chairs", "office chairs"]),
    ("Door Lockers", ["door-lockers", "door lockers"]),
    ("Lockers", ["lockers"]),
    ("Shelving & Racking", ["shelving-racking"]),
    ("Shelving", ["shelving"]),
    ("Desks", ["desks"]),
    ("Tables", ["tables"]),
    ("Chairs", ["chairs"]),
    ("Cupboards", ["cupboards"]),
    ("Pedestals", ["pedestals"]),
    ("Storage", ["storage"]),
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

MATERIALS = [
    "chipboard",
    "melamine",
    "wire-mesh",
    "mesh",
    "steel",
    "wood",
    "perforated",
    "fully-welded",
    "crush-bent",
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
}


# --- Helper 4: Keyword Matching & Search Volume Sorting ---
def find_matched_target_keywords(url_str, curr_title, curr_h1, keyword_data):

    if not keyword_data:
        return []

    context_text = f"{url_str} {curr_title} {curr_h1}".lower()
    matched = []

    for kw_item in keyword_data:
        kw = kw_item["keyword"]
        vol = kw_item["volume"]
        pattern = re.compile(rf"\b{re.escape(kw.lower())}\b")
        if pattern.search(context_text):
            matched.append((kw, vol))

    matched.sort(key=lambda x: x[1], reverse=True)
    return [m[0].title() for m in matched]


# --- Helper 5: Dynamic Taxonomy & Range Parser ---
def parse_url_taxonomy(
    url_str, curr_title="", curr_h1="", matched_keywords=None
):
    if not isinstance(url_str, str):
        return ""

    parsed = urlparse(url_str)
    path_segments = [
        seg
        for seg in parsed.path.split("/")
        if seg and not seg.endswith(".html")
    ]

    if parsed.path.endswith(".html"):
        all_path = parsed.path.replace(".html", "").lower()
    else:
        all_path = parsed.path.lower()

    # A. Product Category Detection
    product_type = ""
    for cat_name, keywords in CATEGORY_PATTERNS:
        if any(kw in all_path for kw in keywords):
            product_type = cat_name
            break

    # B. Duty Grade
    duty = ""
    if "heavy-duty" in all_path or "heavy duty" in all_path:
        duty = "Heavy Duty"
    elif "standard-shelving" in all_path or "standard" in all_path:
        duty = "Standard Duty"

    # C. Colour Detection
    colour = ""
    for c_name, c_kws in COLORS_MAP:
        if any(kw in all_path for kw in c_kws):
            colour = c_name
            break

    # D. Shelves / Door Specs
    shelves_spec = ""
    shelves_match = re.search(
        r"with-(\d+)-(chipboard|melamine|wire-mesh|mesh|steel|wood)-shelves",
        all_path,
    )
    if shelves_match:
        count = shelves_match.group(1)
        mat = shelves_match.group(2).title().replace("-", " ")
        shelves_spec = f"With {count} {mat} Shelves"

    spec_door, spec_tier = "", ""
    d_match = re.search(r"\b(\d+)\s*-?\s*door\b", all_path)
    if d_match:
        spec_door = f"{d_match.group(1)} Door"

    # E. Dimensions & Specs
    dimensions, capacity, age_group = "", "", ""
    dim_match = re.search(r"(\d+wx\d+h|\d+wx\d+dx\d+h)", all_path)
    if dim_match:
        dimensions = dim_match.group(1)

    c_match = re.search(r"\b(\d+kg)\b", all_path)
    if c_match:
        capacity = f"({c_match.group(1).upper()})"

    a_match = re.search(r"(\d+(?:-\d+)?(?:\+)?)-years?(?:-old)?", all_path)
    if a_match:
        age_group = f"({a_match.group(1)} Years)"

    # F. DYNAMIC RANGE EXTRACTION
    clean_path = all_path
    for mat in MATERIALS:
        clean_path = clean_path.replace(mat, "")
    for _, c_kws in COLORS_MAP:
        for kw in c_kws:
            clean_path = clean_path.replace(kw, "")

    clean_path = re.sub(r"with-\d+-[a-z]+-shelves", "", clean_path)
    clean_path = re.sub(r"\b\d+wx\d+h?\b", "", clean_path)
    clean_path = re.sub(r"\b\d+wx\d+dx\d+h?\b", "", clean_path)
    clean_path = re.sub(r"\b\d+-door\b", "", clean_path)
    clean_path = re.sub(r"\b\d+kg\b", "", clean_path)
    clean_path = re.sub(r"\b\d+-\d+-years?-old\b", "", clean_path)
    clean_path = re.sub(r"\b\d+-years?-old\b", "", clean_path)

    path_tokens = re.split(r"[/_-]", clean_path)
    range_tokens = []

    for token in path_tokens:
        token_str = token.strip()
        if (
            token_str
            and token_str not in COMMON_SEO_WORDS
            and (not token_str.isdigit() or len(range_tokens) > 0)
        ):
            formatted = token_str.title()
            if formatted not in range_tokens:
                range_tokens.append(formatted)

    dynamic_range = " ".join(range_tokens).strip()

    # G. Assembly with Keyword Volume Weighting
    parts = []

    if matched_keywords:
        top_keyword = matched_keywords[0]
        parts.append(top_keyword)

    if dynamic_range and not any(
        dynamic_range.lower() in p.lower() for p in parts
    ):
        parts.append(dynamic_range)

    if colour and not any(colour.lower() in p.lower() for p in parts):
        parts.append(colour)
    if duty and not any(duty.lower() in p.lower() for p in parts):
        parts.append(duty)
    if spec_door and not any(spec_door.lower() in p.lower() for p in parts):
        parts.append(spec_door)

    current_str = " ".join(parts).lower()
    if product_type and product_type.lower() not in current_str:
        parts.append(product_type)

    if shelves_spec and not any(
        shelves_spec.lower() in p.lower() for p in parts
    ):
        parts.append(shelves_spec)
    if dimensions:
        parts.append(dimensions)
    if age_group:
        parts.append(age_group)
    if capacity:
        parts.append(capacity)

    raw_h1 = " ".join(parts)
    return deduplicate_title_words(raw_h1)


# --- Helper 6: Disambiguation Engine ---
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
st.subheader("1. Upload Crawl CSV")
uploaded_file = st.file_uploader(
    "Upload Crawl Data CSV", type=["csv", "tsv", "txt"], key="crawl_file"
)

st.subheader("2. Upload Keywords & Search Volumes (Optional)")
keyword_file = st.file_uploader(
    "Upload Target Keywords CSV (Columns: 'Keyword', 'Search Volume')",
    type=["csv", "tsv", "txt"],
    key="kw_file",
)

keyword_data = []

if keyword_file is not None:
    kw_df = load_csv_data(keyword_file)

    kw_col = find_column(
        kw_df, ["Keyword", "Keywords", "Search Term", "Query"]
    )
    vol_col = find_column(
        kw_df, ["Search Volume", "Volume", "Vol", "Monthly Searches"]
    )

    if kw_col:
        for _, r in kw_df.iterrows():
            k_text = str(r[kw_col]).strip()
            v_val = 0
            if vol_col and pd.notnull(r[vol_col]):
                try:
                    v_val = int(
                        float(str(r[vol_col]).replace(",", "").replace(" ", ""))
                    )
                except ValueError:
                    v_val = 0
            if k_text:
                keyword_data.append({"keyword": k_text, "volume": v_val})

        st.success(
            f"Successfully loaded {len(keyword_data):,} target keywords with"
            " search volumes!"
        )
    else:
        st.warning(
            "Could not automatically find a 'Keyword' column in the uploaded"
            " keyword CSV."
        )

if uploaded_file is not None:
    df = load_csv_data(uploaded_file)
    st.success(f"Successfully loaded {len(df):,} URLs from crawl data!")

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
            value=90,
        )

    with set_col2:
        brand_name_input = st.text_input(
            "Add Brand Name To Title 😎",
            value="Furniture At Work",
            help=(
                "Brand name appendeds the end of each title tag. Include a pipe or a hyphen"
            ),
        )

    # Format user brand suffix safely
    raw_brand = brand_name_input.strip()
    if raw_brand:
        if raw_brand.startswith("|") or raw_brand.startswith("-"):
            brand_suffix = f" {raw_brand}"
        else:
            brand_suffix = f" | {raw_brand}"
    else:
        brand_suffix = ""

    if st.button("Generate Rewritten Titles & H1s"):
        with st.spinner("Processing titles and weighting search volumes..."):
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
                    if (title_col != "None" and title_col in df.columns)
                    else ""
                )
                current_h1 = (
                    str(row[h1_col])
                    if (h1_col != "None" and h1_col in df.columns)
                    else ""
                )

                matched_kws = find_matched_target_keywords(
                    url, current_title, current_h1, keyword_data
                )

                raw_h1 = parse_url_taxonomy(
                    url,
                    curr_title=current_title,
                    curr_h1=current_h1,
                    matched_keywords=matched_kws,
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
                    "Top Matched Target Keyword": (
                        matched_kws[0] if matched_kws else "None"
                    ),
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
