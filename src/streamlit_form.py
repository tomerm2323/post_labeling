import streamlit as st
import pandas as pd

# Function to create a custom labeling component
def labeling_component(data, current_row, labels):
    st.write(f"**Text:** {data.iloc[current_row, 0]}")
    label = st.text_input(f"Enter label (0 or 1) for row {current_row + 1}:", key=f"label_{current_row}")

    return label

# Main Streamlit app
def main():
    st.title("Text Labeling Form\n Please enter 1 for pro israel and 0 otherwise")

    csv_file = r"PostsExample.csv"
    data = pd.read_csv(csv_file, encoding="utf8")
    num_entries = len(data)
    labels = []

    for current_row in range(num_entries):
        label = labeling_component(data, current_row, labels)
        labels.append(label)

    # Check if the number of labels provided matches the number of rows
    if len(labels) != num_entries:
        st.error("Please provide labels for all rows before submitting.")
    else:
        # Save the labeled data to a new CSV file
        labeled_data = data.copy()
        labeled_data['Label'] = labels
        st.title("Please review your labels and download")
        @st.experimental_memo
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')

        csv = convert_df(labeled_data)
        st.download_button(
            "Press to Download",
            csv,
            "labeled.csv",
            "text/csv",
            key='download-csv'
        )
        st.write("Labeled Data:")
        st.write(labeled_data)

if __name__ == "__main__":
    main()
