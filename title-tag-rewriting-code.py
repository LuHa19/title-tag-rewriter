import re
from urllib.parse import urlparse
import pandas as pd
import streamlit as st

st.title("Luke's H1 & Title Tag Rewriter Tool ✍️")
st.write(
    "Upload your crawl CSV to programmatically generate clean, unique H1s and"
    " Meta Titles based on URL taxonomy."
)

# 1. File Uploader
uploaded_file = st.file_uploader(
    "Upload CSV File", type=["csv", "tsv", "txt", "numbers"]
)


def find_column(df, candidates):
    for col in df.columns:
        if col.strip().lower() in [c.lower() for c in candidates]:
            return col
    return None


# Helper 1: Remove repeated words within a single title string (protecting specs/dimensions)
def deduplicate_title_words(title_str):
    words = title_str.split()
    seen = set()
    clean_words = []
    # Protect dimension identifiers and connectors from deduplication
    protected = {
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

    for w in words:
        w_lower = re.sub(r"[\(\)\|,]", "", w.lower())
        if w_lower in protected or w_lower not in seen:
            if w_lower not in protected and len(w_lower) > 0:
                seen.add(w_lower)
            clean_words.append(w)
    return " ".join(clean_words)


if uploaded_file is not None:
    try:
        try:
            df = pd.read_csv(
                uploaded_file, encoding="utf-8", sep=None, engine="python"
            )
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            df = pd.read_csv(
                uploaded_file, encoding="latin1", sep=None, engine="python"
            )
    except Exception:
        st.error(
            "⚠️ Unable to read file. If using Apple Numbers or Excel, please go"
            " to File ➔ Export To ➔ CSV before uploading."
        )
        st.stop()

    st.success(f"Successfully loaded {len(df)} URLs!")

    # 2. Column Auto-Detection & Selection
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

    max_title_len = st.number_input(
        "Max Title Tag Length (Characters)",
        min_value=30,
        max_value=100,
        value=70,
    )

    # 3. Processing Engine
    if st.button("Generate Rewritten Titles & H1s"):
        
        # ADDED LOADING SPINNER HERE
        with st.spinner("Analyzing URLs and generating unique tags... Please wait! ⏳"):

            def parse_url_taxonomy(url_str, curr_title="", curr_h1=""):
                if not isinstance(url_str, str):
                    return ""

                parsed = urlparse(url_str)
                path_segments = [
                    seg
                    for seg in parsed.path.split("/")
                    if seg and not seg.endswith(".html")
                ]
                full_path_str = "/".join(path_segments).lower()

                clean_curr_h1 = (
                    curr_h1 if curr_h1 and str(curr_h1).strip() != "0" else ""
                )
                clean_curr_title = (
                    curr_title
                    if curr_title and str(curr_title).strip() != "0"
                    else ""
                )
                full_context = (
                    f"{full_path_str} {clean_curr_h1.lower()}"
                    f" {clean_curr_title.lower()}"
                )

                # A. Product Category Detection
                category_patterns = [
                    ("Classroom Tables", ["classroom-tables", "classroom tables"]),
                    ("Classroom Chairs", ["classroom-chairs", "classroom chairs"]),
                    (
                        "Office Desks",
                        ["office-desks", "office desks", "desks-by-size", "desks"],
                    ),
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
                    ("Screens", ["screens"]),
                    ("Sofas", ["sofas"]),
                    ("Benches", ["benches"]),
                ]

                product_type = ""
                for cat_name, keywords in category_patterns:
                    if any(kw in full_context for kw in keywords):
                        product_type = cat_name
                        break

                # B. Extract Brand / Range
                brand_range = ""
                brands = [
                    ("Probe", ["probe"]),
                    ("Rapid 1", ["rapid-1", "rapid 1"]),
                    ("Rapid 2", ["rapid-2", "rapid 2"]),
                    ("QMP", ["qmp"]),
                    ("Elite", ["elite"]),
                    ("Pure", ["pure"]),
                    ("Educate", ["educate"]),
                    ("Value Line", ["value-line", "value line"]),
                    ("Everyday", ["everyday"]),
                    ("Titan", ["titan"]),
                    ("Hille", ["hille"]),
                    ("Bisley", ["bisley"]),
                    ("Tully", ["tully"]),
                    ("Progress", ["progress"]),
                ]
                for b_name, b_kws in brands:
                    if any(kw in full_path_str for kw in b_kws):
                        brand_range = b_name
                        break

                # C. Extract Material / Finish
                material_finish = ""
                materials = [
                    ("Chipboard", ["chipboard"]),
                    ("Galvanised", ["galvanized", "galvanised"]),
                    ("Melamine", ["melamine"]),
                    ("Wire Mesh", ["wire-mesh", "wire mesh"]),
                    ("Perforated", ["perforated"]),
                    ("Vision Panel", ["vision-panel", "vision"]),
                    ("Fully Welded", ["fully-welded", "fully welded"]),
                    ("Crush Bent", ["crush-bent", "crush bent"]),
                ]
                for m_name, m_kws in materials:
                    if any(kw in full_path_str for kw in m_kws):
                        material_finish = m_name
                        break

                # D. Extract Specs
                spec_door, spec_tier, dimensions, age_group, capacity = (
                    "",
                    "",
                    "",
                    "",
                    "",
                )

                for seg in path_segments:
                    seg_lower = seg.lower()

                    d_match = re.search(r"\b(\d+)\s*-?\s*door\b", seg_lower)
                    if d_match:
                        spec_door = f"{d_match.group(1)} Door"

                    t_match = re.search(
                        r"\b(\d+)\s*-?\s*(tier|shelves)\b", seg_lower
                    )
                    if t_match:
                        spec_tier = f"{t_match.group(1)} Tier"

                    c_match = re.search(r"\b(\d+kg)\b", seg_lower)
                    if c_match:
                        capacity = f"({c_match.group(1).upper()})"

                    a_match = re.search(
                        r"(\d+(?:-\d+)?(?:\+)?)-years?(?:-old)?", seg_lower
                    )
                    if a_match:
                        age_group = f"({a_match.group(1)} Years)"

                    if re.search(r"\d+wx\d+h", seg_lower) or re.search(
                        r"\d+wx\d+dx\d+h", seg_lower
                    ):
                        dim_str = seg_lower
                        dim_str = re.sub(r"[-_]*cm$", "", dim_str)
                        dim_str = re.sub(r"[-_]*mm$", "", dim_str)

                        d3 = re.search(r"(\d+)wx(\d+)dx(\d+)h", dim_str)
                        d2 = re.search(r"(\d+)wx(\d+)h", dim_str)
                        if d3:
                            dimensions = (
                                f"{d3.group(1)}w x {d3.group(2)}d x"
                                f" {d3.group(3)}h cm".upper()
                            )
                        elif d2:
                            dimensions = f"{d2.group(1)}w x {d2.group(2)}h mm".upper()

                # E. Build Title Parts
                title_parts = []
                if brand_range:
                    title_parts.append(brand_range)
                if material_finish:
                    title_parts.append(material_finish)
                if spec_door:
                    title_parts.append(spec_door)
                if spec_tier:
                    title_parts.append(spec_tier)

                current_title_str = " ".join(title_parts)
                if product_type:
                    if product_type.lower() not in current_title_str.lower():
                        if "door" in current_title_str.lower() and product_type.lower() in [
                            "lockers",
                            "door lockers",
                        ]:
                            title_parts.append("Lockers")
                        else:
                            title_parts.append(product_type)
                elif not title_parts and path_segments:
                    title_parts.append(
                        path_segments[-1].replace("-", " ").title()
                    )

                if dimensions:
                    title_parts.append(dimensions)
                if age_group:
                    title_parts.append(age_group)
                if capacity:
                    title_parts.append(capacity)

                raw_h1 = " ".join(title_parts)
                raw_h1 = deduplicate_title_words(raw_h1)

                return raw_h1

            # Helper 2: Cross-URL Disambiguation Engine
            def ensure_unique_title(
                url_str, base_h1, brand_suffix, max_len, seen_titles
            ):
                full_title = f"{base_h1}{brand_suffix}"

                # If title length exceeds max, truncate body cleanly
                if len(full_title) > max_len:
                    max_body_len = max_len - len(brand_suffix)
                    if max_body_len > 10:
                        truncated_body = base_h1[:max_body_len].rsplit(" ", 1)[0]
                        full_title = f"{truncated_body}{brand_suffix}"
                    else:
                        full_title = full_title[:max_len]

                # Unique Check 1: Title is already unique across dataset
                if full_title not in seen_titles:
                    seen_titles.add(full_title)
                    return base_h1, full_title

                # Unique Check 2: Try adding parent URL folder differentiators
                parsed = urlparse(url_str)
                segments = [
                    s.replace("-", " ").title()
                    for s in parsed.path.split("/")
                    if s and not s.endswith(".html")
                ]

                differentiating_h1 = base_h1
                for seg in reversed(segments[:-1]):
                    diff_words = [
                        w
                        for w in seg.split()
                        if w.lower() not in base_h1.lower()
                        and w.lower()
                        not in [
                            "lockers",
                            "tables",
                            "desks",
                            "chairs",
                            "metric",
                            "furniture",
                        ]
                    ]
                    if diff_words:
                        diff_text = " ".join(diff_words)
                        differentiating_h1 = f"{diff_text} {base_h1}"
                        differentiating_h1 = deduplicate_title_words(
                            differentiating_h1
                        )

                        candidate_title = f"{differentiating_h1}{brand_suffix}"
                        if len(candidate_title) > max_len:
                            max_body_len = max_len - len(brand_suffix)
                            truncated_body = differentiating_h1[
                                :max_body_len
                            ].rsplit(" ", 1)[0]
                            candidate_title = f"{truncated_body}{brand_suffix}"

                        if candidate_title not in seen_titles:
                            seen_titles.add(candidate_title)
                            return differentiating_h1, candidate_title

                # Unique Check 3: Fallback variant numbering for identical URL parameters/paths
                variant_counter = 2
                while True:
                    variant_h1 = f"{base_h1} (Variant {variant_counter})"
                    candidate_title = f"{variant_h1}{brand_suffix}"
                    if len(candidate_title) > max_len:
                        max_body_len = max_len - len(brand_suffix)
                        truncated_body = variant_h1[:max_body_len].rsplit(" ", 1)[0]
                        candidate_title = f"{truncated_body}{brand_suffix}"

                    if candidate_title not in seen_titles:
                        seen_titles.add(candidate_title)
                        return variant_h1, candidate_title
                    variant_counter += 1

            results = []
            seen_recommended_titles = set()
            brand_suffix = " | Furniture At Work"
            
            # ADDED PROGRESS BAR AND STATUS TEXT HERE
            total_rows = len(df)
            progress_bar = st.progress(0)
            status_text = st.empty()

            for index, row in df.iterrows():
                
                # Update progress visually
                pct_complete = int(((index + 1) / total_rows) * 100)
                status_text.text(f"Processing row {index + 1} of {total_rows} ({pct_complete}%)...")
                progress_bar.progress((index + 1) / total_rows)
                
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
                    "Current Title Tag": current_title,
                    "Recommended Title Tag": final_title,
                    "Current H1": current_h1,
                    "Recommended H1": final_h1,
                    "Title Tag Length": len(final_title),
                })
            
            # Clear the loading text when finished
            status_text.empty()

        # Render Results
        output_df = pd.DataFrame(results)

        st.subheader("🎉 Generated Optimization Table")
        st.dataframe(output_df)

        # 4. Download Export
        csv_data = output_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Rewritten Titles & H1s CSV",
            data=csv_data,
            file_name="rewritten_titles_and_h1s.csv",
            mime="text/csv",
        )
