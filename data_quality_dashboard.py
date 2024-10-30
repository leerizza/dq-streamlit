# Import Libraries
import pandas as pd
import great_expectations as ge
import streamlit as st
import altair as alt

# Step 1: Load Data
data = pd.read_csv("cerita_praktik_2.csv")
df = pd.DataFrame(data)

# Step 2: Convert DataFrame to Great Expectations DataFrame
ge_df = ge.from_pandas(df)

# Columns to check for missing values, uniqueness, and validity
columns_to_check_missing = [
    'content_id', 'nama', 'median_content_location', 'num_cp_words',
    'content_type', 'title', 'creator_email', 'category_string',
    'npsn', 'nama_satuan_pendidikan', 'province_name', 'city_name'
]
columns_to_check_uniqueness = ['content_id']
columns_to_check_validity = {
    'creator_email': r"[^@]+@[^@]+\.[^@]+",  # Email format check
    #'age': (18, 65)  # Age validity range
}

# Step 3: Define Expectations for Missing Values
for column in columns_to_check_missing:
    ge_df.expect_column_values_to_not_be_null(column)

# Define Uniqueness Expectation
for column in columns_to_check_uniqueness:
    ge_df.expect_column_values_to_be_unique(column)

# Define Validity Expectations (email regex and age range)
for column, rule in columns_to_check_validity.items():
    if isinstance(rule, tuple):  # Apply range check for numeric columns
        ge_df.expect_column_values_to_be_between(column, min_value=rule[0], max_value=rule[1])
    else:  # Apply regex match for string columns
        ge_df.expect_column_values_to_match_regex(column, rule)

# Step 4: Row-level Uniqueness Check
# Identify duplicate rows (row-level uniqueness check)
duplicate_rows = df[df.duplicated(keep=False)]  # 'keep=False' shows all duplicates

# Check if any duplicate rows are found
row_level_uniqueness_success = duplicate_rows.empty
row_level_uniqueness_failed_count = len(duplicate_rows)

# Display the list of duplicate rows if any
if not row_level_uniqueness_success:
    st.write("### Duplicate Rows Found (Row-level Uniqueness Check)")
    st.write(duplicate_rows)

# Step 5: Run Validation and Process Results
results = ge_df.validate()

# Prepare summary of validation results
validation_summary = {
    "Column Name": [],
    "Expectation Type": [],
    "Success": [],
    "Failed Count": [],
    "Failure Percentage": []
}

# Process validation results for each expectation
for result in results['results']:
    column_name = result['expectation_config']['kwargs'].get('column', "N/A")
    expectation_type = result['expectation_config']['expectation_type']
    success = result['success']
    failed_count = result['result'].get('unexpected_count', 0)
    total_count = len(df)
    failure_percentage = (failed_count / total_count) * 100 if total_count > 0 else 0
    
    # Append result data to summary
    validation_summary["Column Name"].append(column_name)
    validation_summary["Expectation Type"].append(expectation_type)
    validation_summary["Success"].append("Yes" if success else "No")
    validation_summary["Failed Count"].append(failed_count)
    validation_summary["Failure Percentage"].append(f"{failure_percentage:.2f}%")

# Add row-level uniqueness check to validation summary
validation_summary["Column Name"].append("All Columns (Row-level)")
validation_summary["Expectation Type"].append("Row-level Uniqueness")
validation_summary["Success"].append("Yes" if row_level_uniqueness_success else "No")
validation_summary["Failed Count"].append(row_level_uniqueness_failed_count)
validation_summary["Failure Percentage"].append(f"{(row_level_uniqueness_failed_count / len(df)) * 100:.2f}%" if len(df) > 0 else "0%")

# Convert validation summary to DataFrame for display
validation_df = pd.DataFrame(validation_summary)

# Step 6: Streamlit Dashboard
st.title("Data Quality Monitoring Dashboard")
st.subheader("Overview of Data Quality Checks")

# Display columns checked for missing values, uniqueness, and validity
st.write("### Columns Checked for Missing Values, Uniqueness, and Validity:")
st.write(", ".join(columns_to_check_missing + columns_to_check_uniqueness + list(columns_to_check_validity.keys())))

# Display Validation Summary Table
st.write("### Validation Summary")
st.write("This table shows the outcome of each expectation check, including missing values, uniqueness, validity, and row-level uniqueness.")
st.dataframe(validation_df)

# Visualization: Data Quality Metrics by Column
st.write("### Data Quality Metrics by Column")
# Bar chart: Failed Count by Column
chart_failed = alt.Chart(validation_df).mark_bar(color='orange').encode(
    x=alt.X('Column Name', sort='-y'),
    y='Failed Count'
).properties(title="Failed Counts by Column")

# Bar chart: Failure Percentage by Column
chart_failure_pct = alt.Chart(validation_df).mark_bar(color='red').encode(
    x=alt.X('Column Name', sort='-y'),
    y='Failure Percentage'
).properties(title="Failure Percentage by Column")

# Display charts in Streamlit
st.altair_chart(chart_failed, use_container_width=True)
st.altair_chart(chart_failure_pct, use_container_width=True)

# Interpretation and Recommendations
st.write("### Interpretation and Recommendations")
st.write("""
- **Uniqueness** checks ensure critical identifiers (like 'content_id') are unique, while row-level uniqueness prevents exact duplicate rows.
- **Validity** checks ensure data meets specified formats or ranges (e.g., email format, age range).
- **Row-level Uniqueness** check reveals any identical rows across all columns, which may indicate data duplication errors.
- Consider addressing missing values, duplicates, and incorrect formats/ranges by:
    - Reviewing and correcting data entry.
    - Adding validation steps in upstream processes.
    - Applying data deduplication or transformation strategies as necessary.
""")
