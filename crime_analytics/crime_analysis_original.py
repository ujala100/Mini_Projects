import pandas as pd
import numpy as np

# Alias operations: Using 'pd' for pandas and 'np' for numpy
file_path = 'Downloads/Crime_Data_from_2020_to_Present.csv'

# Import operation
df = pd.read_csv(file_path)
print(f"Dataset loaded with {df.shape[0]} rows.")
display(df.head(2))

# Data Preprocessing & Constraints
# Converting date strings to datetime objects
df['Date Rptd'] = pd.to_datetime(df['Date Rptd'])
df['DATE OCC'] = pd.to_datetime(df['DATE OCC'])

# Identifier function: Create a unique ID if one didn't exist (using index as a base)
def generate_custom_id(index):
    return f"CRIME_EVENT_{index}"

df['Internal_ID'] = df.index.map(generate_custom_id)

# Handling missing values (Constraint: Victim Age must be valid)
df = df.dropna(subset=['Vict Age'])
df = df[df['Vict Age'] > 0]  # Mathematical operation for filtering

print("Preprocessing complete.")

# String Operations
# Standardizing Area Names and extracting crime categories
df['AREA NAME'] = df['AREA NAME'].str.upper().str.strip()
df['Crime_Category'] = df['Crm Cd Desc'].str.split(' ').str[0]

display(df[['AREA NAME', 'Crime_Category']].head())

# Statistical functions, Quantile and Percentile
mean_age = df['Vict Age'].mean()
median_age = df['Vict Age'].median()
quantile_75 = df['Vict Age'].quantile(0.75)
percentile_90 = np.percentile(df['Vict Age'], 90)

print(f"Mean Age: {mean_age:.2f}")
print(f"75th Percentile: {quantile_75}")
print(f"90th Percentile: {percentile_90}")

# Aggregate functions
crime_summary = df.groupby('AREA NAME').agg({
    'Vict Age': ['mean', 'min', 'max'],
    'DR_NO': 'count'
}).rename(columns={'count': 'Total_Crimes'})

display(crime_summary.head())

# Automated dataset operation (Dynamic Trigger)
def automated_priority_trigger(dataframe):
    """
    Automatically flags areas based on crime volume.
    Areas with crime counts above the 75th percentile are 'HIGH' priority.
    """
    counts = dataframe['AREA NAME'].value_counts()
    threshold = counts.quantile(0.75)
    high_priority_areas = counts[counts >= threshold].index.tolist()
    print(f"Trigger identified {len(high_priority_areas)} high-priority areas based on data distribution.")
    dataframe['Priority'] = dataframe['AREA NAME'].apply(
        lambda x: 'HIGH' if x in high_priority_areas else 'STANDARD'
    )
    return dataframe

# Run the automated trigger
df = automated_priority_trigger(df)

# Display the results of the automated flagging
display(df[['AREA NAME', 'Priority']].drop_duplicates())

# Export operation
df.to_csv('processed_crime_data_with_priority.csv', index=False)
print("Exported processed data to processed_crime_data_with_priority.csv")

# User Input: Check Priority for a Specific Area
def check_area_priority(dataframe):
    user_input = input("Enter Area Name to check priority: ").upper().strip()
    result = dataframe[dataframe['AREA NAME'] == user_input]['Priority'].unique()
    if len(result) > 0:
        print(f"The area '{user_input}' is classified as: {result[0]} priority.")
    else:
        print(f"Area '{user_input}' not found in the dataset. Please check the spelling.")

check_area_priority(df)
