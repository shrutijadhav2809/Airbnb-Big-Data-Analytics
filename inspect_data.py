
import pandas as pd

df = pd.read_csv("final_data.csv")

# Remove duplicate records
df = df.drop_duplicates()

# Standardize text columns
for col in ["name", "location", "state", "country", "roomType"]:
    if col in df.columns:
        df[col] = df[col].astype("string").str.strip()

# Convert numeric columns
for col in ["price", "stars", "numberOfGuests", "latitude", "longitude"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Save cleaned dataset
df.to_csv("airbnb_cleaned.csv", index=False)

print("Dataset cleaning completed!")
print("Rows and columns:", df.shape)
print("Missing values after cleaning:")
print(df.isnull().sum())
print("\nCleaned dataset saved as airbnb_cleaned.csv")


print("\n--- CLEANED DATASET CHECK ---")
cleaned = pd.read_csv("airbnb_cleaned.csv")

print("Shape:", cleaned.shape)
print("Missing values:", cleaned.isnull().sum().sum())
print("Duplicate records:", cleaned.duplicated().sum())

print("\n--- LISTINGS BY STATE ---")
print(cleaned["state"].value_counts().head(10))
