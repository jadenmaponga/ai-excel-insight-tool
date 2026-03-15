import pandas as pd

def clean_dataset(file):
    changes = []

    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    changes.append(f"Loaded {df.shape[0]} rows x {df.shape[1]} columns")

    df.columns = (df.columns.str.strip().str.lower()
                  .str.replace(r"[^\w\s]", "", regex=True)
                  .str.replace(r"\s+", "_", regex=True))

    df.dropna(how="all", inplace=True)
    df.dropna(axis=1, how="all", inplace=True)

    dupes = df.duplicated().sum()
    if dupes:
        df.drop_duplicates(inplace=True)
        changes.append(f"Removed {dupes} duplicate row(s)")

    date_keywords = ["date", "time", "dt", "created", "updated", "ordered"]
    for col in df.columns:
        if any(kw in col for kw in date_keywords):
            converted = pd.to_datetime(df[col], errors="coerce")
            valid_ratio = converted.notna().sum() / max(len(df), 1)
            if valid_ratio >= 0.3:
                df[col] = converted.dt.strftime('%Y-%m-%d')
                changes.append(f"Standardised date column '{col}'")

    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().astype(str)
            if sample.str.contains(r"[\$£€%]", regex=True).any():
                cleaned = (sample.str.replace(r"[\$£€,%]", "", regex=True)
                           .str.replace(",", "", regex=False).str.strip())
                try:
                    df[col] = pd.to_numeric(cleaned, errors="raise")
                    changes.append(f"Converted '{col}' to numeric")
                except Exception:
                    pass

    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().astype(str)
            if sample.str.len().mean() > 2:
                df[col] = df[col].astype(str).str.strip().str.title()
                df[col] = df[col].replace("Nan", pd.NA)

    num_cols = df.select_dtypes(include=["number"]).columns
    txt_cols = df.select_dtypes(include=["object"]).columns

    missing_num = df[num_cols].isna().sum().sum()
    if missing_num:
        df[num_cols] = df[num_cols].fillna(0)
        changes.append(f"Filled {missing_num} missing numeric value(s) with 0")

    for col in txt_cols:
        if df[col].isna().sum() > 0:
            df[col] = df[col].fillna("Unknown")

    qty_candidates = [c for c in df.columns if any(k in c for k in ["qty","quantity","units","count"])]
    price_candidates = [c for c in df.columns if any(k in c for k in ["price","rate","cost","unit_price"])]
    total_candidates = [c for c in df.columns if any(k in c for k in ["total","revenue","amount","sales"])]

    if qty_candidates and price_candidates and not total_candidates:
        q_col = qty_candidates[0]
        p_col = price_candidates[0]
        df["total_revenue"] = (
            pd.to_numeric(df[q_col], errors="coerce").fillna(0)
            * pd.to_numeric(df[p_col], errors="coerce").fillna(0)
        ).round(2)
        changes.append(f"Auto-calculated total_revenue = {q_col} x {p_col}")

    changes.append(f"Final: {df.shape[0]} rows x {df.shape[1]} columns")
    return df, changes
