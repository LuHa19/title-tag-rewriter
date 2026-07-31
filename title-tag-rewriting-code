import streamlit as st
import pandas as pd
import re
from urllib.parse import urlparse

st.title("Luke's Dynamic H1 & Title Tag Rewriter ✍️")
st.write("Upload your duplicate H1/Title export CSV to programmatically generate unique H1s and Meta Titles (max 70 chars).")

uploaded_file = st.file_uploader("Upload CSV File", type=["csv", "tsv", "txt"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
    except Exception:
        df = pd.read_csv(uploaded_file)

    st.success(f"Successfully loaded {len(df)} URLs!")

    max_title_len = st.number_input("Max Title Tag Length (Characters)", min_value=30, max_value=100, value=70)

    if st.button("Generate Unique H1s & Title Tags"):
        
        def format_slug_text(slug):
            text = slug.replace('-', ' ').replace('_', ' ')
            text = re.sub(r'\.html$', '', text)
            text = re.sub(r'\b(\d+)\s*wx\s*(\d+)\s*dx\s*(\d+)\s*h\b', r'\1w x \2d x \3h', text)
            text = re.sub(r'\b(\d+)\s*wx\s*(\d+)\s*h\b', r'\1w x \2h', text)
            return text.strip().title()

        def parse_url_taxonomy(url_str, max_len=70):
            if not isinstance(url_str, str):
                return "", ""
            
            parsed = urlparse(url_str)
            path_segments = [seg for seg in parsed.path.split('/') if seg and not seg.endswith('.html')]
            
            brand_range = ""
            material_finish = ""
            capacity = ""
            age_group = ""
            dimensions = ""
            
            for seg in path_segments:
                seg_lower = seg.lower()
                
                # Capacity
                if re.search(r'\d+kg', seg_lower):
                    cap_match = re.search(r'(\d+kg)', seg_lower)
                    if cap_match:
                        capacity = f"({cap_match.group(1).upper()})"
                
                # Material
                if 'chipboard' in seg_lower:
                    material_finish = "Chipboard"
                elif 'galvanized' in seg_lower or 'galvanised' in seg_lower:
                    material_finish = "Galvanised"
                elif 'melamine' in seg_lower:
                    material_finish = "Melamine"
                elif 'mesh' in seg_lower:
                    material_finish = "Wire Mesh"
                elif 'perforated' in seg_lower:
                    material_finish = "Perforated"
                elif 'vision' in seg_lower:
                    material_finish = "Vision Panel"

                # Brand / Range
                if 'probe' in seg_lower:
                    brand_range = "Probe"
                elif 'rapid-1' in seg_lower:
                    brand_range = "Rapid 1"
                elif 'rapid-2' in seg_lower:
                    brand_range = "Rapid 2"
                elif 'qmp' in seg_lower:
                    brand_range = "QMP"
                elif 'elite' in seg_lower:
                    brand_range = "Elite"
                elif 'pure' in seg_lower:
                    brand_range = "Pure"
                elif 'educate' in seg_lower:
                    brand_range = "Educate"
                elif 'value-line' in seg_lower:
                    brand_range = "Value Line"
                elif 'everyday' in seg_lower:
                    brand_range = "Everyday"

                # Age Groups
                if re.search(r'\d+-\d+-years', seg_lower) or re.search(r'\d+-years', seg_lower):
                    age_match = re.search(r'(\d+[-+]*\d*)\s*years?', seg_lower.replace('-', ' '))
                    if age_match:
                        age_group = f"({age_match.group(1)} Years)"

                # Dimensions
                if re.search(r'\d+wx\d+h', seg_lower) or re.search(r'\d+wx\d+dx\d+h', seg_lower):
                    dim_text = seg_lower.replace('cm', '').replace('mm', '')
                    dim_text = re.sub(r'(\d+)wx(\d+)dx(\d+)h', r'\1w x \2d x \3h cm', dim_text)
                    dim_text = re.sub(r'(\d+)wx(\d+)h', r'\1w x \2h mm', dim_text)
                    dimensions = dim_text.upper()

            # Base Category Name from last path segment
            last_segment = path_segments[-1] if path_segments else ""
            base_name = format_slug_text(last_segment)
            base_name = re.sub(r'\b\d+Wx\d+H\b', '', base_name, flags=re.IGNORECASE)
            base_name = re.sub(r'\b\d+Wx\d+Dx\d+H\b', '', base_name, flags=re.IGNORECASE)

            # Reconstruct Proposed H1
            h1_components = [brand_range, material_finish, base_name, dimensions, age_group, capacity]
            proposed_h1 = " ".join([c for c in h1_components if c]).strip()
            proposed_h1 = re.sub(r'\s+', ' ', proposed_h1)

            # Construct Title Tag
            brand_suffix = " | Furniture At Work"
            full_title = f"{proposed_h1}{brand_suffix}"

            # Enforce 70-character limit
            if len(full_title) > max_len:
                max_body_len = max_len - len(brand_suffix)
                if max_body_len > 10:
                    # Truncate body at last whole word
                    truncated_body = proposed_h1[:max_body_len].rsplit(' ', 1)[0]
                    proposed_title = f"{truncated_body}{brand_suffix}"
                else:
                    proposed_title = full_title[:max_len]
            else:
                proposed_title = full_title

            return proposed_h1, proposed_title

        # Determine URL column
        url_col = df.columns[0]
        for col in df.columns:
            if 'http' in str(df[col].iloc[0]):
                url_col = col
                break

        results = []
        for _, row in df.iterrows():
            url = str(row[url_col])
            new_h1, new_title = parse_url_taxonomy(url, max_len=max_title_len)
            
            results.append({
                'URL': url,
                'Current Title': row.get(df.columns[2], ''),
                'Proposed New H1': new_h1,
                'Proposed Title Tag': new_title,
                'Title Length': len(new_title)
            })

        output_df = pd.DataFrame(results)
        
        st.dataframe(output_df)

        # Download CSV
        csv_data = output_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Rewritten CSV",
            data=csv_data,
            file_name="rewritten_titles_and_h1s.csv",
            mime="text/csv"
        )
