import streamlit as st
from datetime import datetime, timedelta
import random
import matplotlib.pyplot as plt

# Helper functions to generate XML content
def generate_concurrent_xml(records):
    xml_content = "<ConcurrentRecords>\n"
    for record in records:
        xml_content += f"  <Record>\n"
        xml_content += f"    <Date>{record['date']}</Date>\n"
        xml_content += f"    <Value>{record['value']}</Value>\n"
        xml_content += f"  </Record>\n"
    xml_content += "</ConcurrentRecords>"
    return xml_content

def generate_denial_xml(records):
    xml_content = "<DenialRecords>\n"
    for record in records:
        xml_content += f"  <Record>\n"
        xml_content += f"    <Date>{record['date']}</Date>\n"
        xml_content += f"    <Value>{record['value']}</Value>\n"
        xml_content += f"  </Record>\n"
    xml_content += "</DenialRecords>"
    return xml_content

# Helper function to plot records
def plot_records(concurrent_records, denial_records):
    fig, ax = plt.subplots(figsize=(12, 6))

    # Extract dates and values for concurrent records
    concurrent_dates = [record["date"] for record in concurrent_records]
    concurrent_values = [record["value"] for record in concurrent_records]

    # Extract dates and values for denial records
    denial_dates = [record["date"] for record in denial_records]
    denial_values = [record["value"] for record in denial_records]

    # Plot concurrent records as a line graph
    ax.plot(concurrent_dates, concurrent_values, label="Concurrent Records", color="blue", linewidth=2)

    # Plot denial records as a bar graph
    ax.bar(denial_dates, denial_values, label="Denial Records", color="red", alpha=0.6)

    # Formatting the graph
    ax.set_title("Concurrent and Denial Records Visualization", fontsize=16)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Value", fontsize=12)
    ax.legend(loc="upper left")
    plt.xticks(rotation=45, fontsize=8)
    plt.tight_layout()

    return fig

# Streamlit app logic
st.title("Record Generation App")

# User inputs
quantity = st.number_input("Enter the threshold (Quantity):", min_value=1, step=1)
num_records = st.number_input("Enter the number of records below the threshold:", min_value=1, step=1)
range_start = st.number_input("Enter the start of denial range:", min_value=1, step=1)
range_end = st.number_input("Enter the end of denial range:", min_value=range_start, step=1)
date_range = st.date_input("Select start and end dates:", [datetime.today(), datetime.today() + timedelta(days=30)])
generate_button = st.button("Generate Records")

if generate_button:
    # Initialization
    start_date = date_range[0]
    end_date = date_range[1]
    total_days = (end_date - start_date).days + 1

    records = []
    current_date = start_date
    increment_value = quantity // num_records
    value = increment_value
    overpeak_count = random.randint(range_start, range_end)
    original_overpeak_count = overpeak_count
    phase = "increment"  # Start with the increment phase
    median_reached = False
    double_decrement_next = False  # For even overpeak records

    while current_date <= end_date:
        if phase == "increment":
            # Incremental records (B1)
            records.append({"date": current_date.strftime("%Y-%m-%d"), "value": value, "type": "B1"})
            if value >= quantity:
                value = quantity  # Set the value to the peak (100)
                phase = "denial"  # Transition to denial phase
                overpeak_count = random.randint(range_start, range_end)
            else:
                value += increment_value
        elif phase == "denial" and overpeak_count > 0:
            # Denial records (B2)
            excess_value = value - quantity  # Calculate the excess over the threshold
            records.append({"date": current_date.strftime("%Y-%m-%d"), "value": excess_value, "type": "B2"})
            overpeak_count -= 1

            if not median_reached:
                if overpeak_count == (original_overpeak_count // 2) - 1:  # Second median for even counts
                    median_reached = True
                    double_decrement_next = True
                elif overpeak_count == (original_overpeak_count // 2):  # Single median for odd counts
                    median_reached = True

            if not median_reached:
                value += increment_value
            else:
                if double_decrement_next:
                    value -= 2 * increment_value
                    double_decrement_next = False
                else:
                    value -= increment_value
        elif phase == "decrement":
            # Decremental records (B1)
            records.append({"date": current_date.strftime("%Y-%m-%d"), "value": value, "type": "B1"})
            if value <= quantity / 2:  # Stop decrementing at half-threshold
                phase = "increment"
                value = increment_value  # Restart increment phase
            else:
                value -= increment_value

        if phase == "denial" and overpeak_count <= 0:
            phase = "decrement"

        # Increment date to prevent skipping
        current_date += timedelta(days=1)

    # Separate concurrent and denial records
    concurrent_records = [r for r in records if r['type'] == 'B1']
    denial_records = [r for r in records if r['type'] == 'B2']

    # Generate XML strings
    st.session_state["concurrent_xml"] = generate_concurrent_xml(concurrent_records)
    st.session_state["denial_xml"] = generate_denial_xml(denial_records)

    # Display record counts
    st.header("Generated Records Summary")
    st.write(f"Total Records: {len(records)}")
    st.write(f"Concurrent Records (B1): {len(concurrent_records)}")
    st.write(f"Denial Records (B2): {len(denial_records)}")

    # Generate and display the plot
    st.subheader("Visualization of Generated Records")
    fig = plot_records(concurrent_records, denial_records)
    st.pyplot(fig)

# Buttons to download the files
if "concurrent_xml" in st.session_state:
    st.download_button(
        "Download Concurrent XML",
        st.session_state["concurrent_xml"],
        file_name="concurrent_records.xml"
    )

if "denial_xml" in st.session_state:
    st.download_button(
        "Download Denial XML",
        st.session_state["denial_xml"],
        file_name="denial_records.xml"
    )
