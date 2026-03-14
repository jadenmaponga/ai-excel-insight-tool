import pandas as pd

def clean_dataset(file_path):

    # Load dataset
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    print("\nOriginal dataset shape:", df.shape)

    # Standardize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Remove duplicate rows
    df = df.drop_duplicates()

    # Fill missing numeric values with 0
    numeric_cols = df.select_dtypes(include=['float64','int64']).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    # Fill missing text values with 'Unknown'
    text_cols = df.select_dtypes(include=['object']).columns
    df[text_cols] = df[text_cols].fillna("Unknown")

    # Remove completely empty rows
    df = df.dropna(how='all')

    print("Cleaned dataset shape:", df.shape)

    return df


if __name__ == "__main__":

    file = "sales.xlsx"

    cleaned_df = clean_dataset(file)

    print("\nPreview of cleaned data:")
    print(cleaned_df.head())