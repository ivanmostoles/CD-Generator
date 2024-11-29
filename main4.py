import streamlit as st
import random
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

# Helper function to generate XML content for Concurrent Records
def generate_concurrent_xml(records):
    root = ET.Element("ConcurrentRecords")
    for record in records:
        entry = ET.SubElement(root, "Record")
        ET.SubElement(entry, "Date").text = record['date']
        ET.SubElement(entry, "Value").text = str(record['value'])
    return ET.tostring(root, encoding='utf-8', method='xml').decode()

# Helper function to generate XML content for Denial Records
def generate_denial_xml(records):
    root = ET.Element("DenialRecords")
    for record in records:
        entry = ET.SubElement(root, "Record")
        ET.SubElement(entry, "Date").text = record['date']
        ET.SubElement(entry, "Value").text = str(record['value'])
    return ET.tostring(root, encoding='utf-8', method='xml').decode()

# Streamlit app
st.title("Concurrent and Denial Record Generator with Horizontal Threshold Line")

# Input Section
st.header("Input Parameters")
date_range = st.date_input("Select Date Range", [datetime.today(), datetime.today()])
quantity = st.number_input("Enter Quantity (Threshold/Peak Value)", min_value=1, step=1)
num_records = st.number_input("Enter Total Number of Records (Concurrent Usage)", min_value=1, step=1)
range_start = st.number_input("Overpeak Range Start", min_value=1, step=1)
range_end = st.number_input("Overpeak Range End", min_value=range_start, step=1)
generate_button = st.button("Generate Records")

# Generate Records
if generate_button:
    # Initialization
    start_date = date_range[0]
    end_date = date_range[1]
    total_days = (end_date - start_date).days + 1

    records = []
    current_date = start_date
    increment_value = quantity // num_records
    value = increment_value
    overpeak_count = random.randint(range_start, range_end)  # Determine the number of denial records
    phase = "increment"  # Start with the increment phase
    flat_days = 0  # Number of flat days for the flat phase

    denial_records = []  # Store Denial Records (B2)
    concurrent_peak_records = []  # Temporary storage for Concurrent Peak Records

    while current_date <= end_date:
        if phase == "increment":
            # Incremental records (B1)
            records.append({"date": current_date.strftime("%Y-%m-%d"), "value": value, "type": "B1"})
            value += increment_value
            if value >= quantity:
                value = quantity  # Cap at the peak value
                # Randomize next behavior at the peak
                next_behavior = random.choice(["flat", "decrement"])
                if next_behavior == "flat":
                    phase = "flat"
                    flat_days = random.randint(2, 5)  # Randomize the flat period
                    flat_value = value  # Keep value constant at the peak
                else:
                    phase = "decrement"
                    value -= increment_value  # Start decrementing from below the peak

        elif phase == "flat":
            # Generate flat values only at the peak
            for _ in range(flat_days):
                records.append({"date": current_date.strftime("%Y-%m-%d"), "value": flat_value, "type": "B1"})
                current_date += timedelta(days=1)
            # After the flat phase, transition to the decrement phase
            phase = "decrement"
            value -= increment_value  # Start decrementing after the flat phase

        elif phase == "decrement":
            # Decremental records (B1)
            records.append({"date": current_date.strftime("%Y-%m-%d"), "value": value, "type": "B1"})
            if value <= quantity / 2:  # Reached half-threshold
                phase = "increment"  # Resume incrementing
                value += increment_value  # Start incrementing from last value
            else:
                value -= increment_value  # Continue decrementing if above half-threshold

        # Increment date
        current_date += timedelta(days=1)

    # Generate Denial Records
    for record in records:
        if record["value"] == quantity:
            denial_records.append({"date": record["date"], "value": increment_value})

    # Generate XML strings
    concurrent_records = [r for r in records if r['type'] == 'B1']  # Already in proper sequence
    st.session_state["concurrent_xml"] = generate_concurrent_xml(concurrent_records)
    st.session_state["denial_xml"] = generate_denial_xml(denial_records)

    # Display record counts
    st.header("Generated Records Summary")
    st.write(f"Total Records: {len(records)}")
    st.write(f"Concurrent Records (B1 + B2): {len(concurrent_records)}")
    st.write(f"Denial Records (B2): {len(denial_records)}")

    # Generate a plot
    st.header("Graphical Representation")

    # Extract values and dates for concurrent and denial records
    concurrent_dates = [r['date'] for r in concurrent_records]
    concurrent_values = [r['value'] for r in concurrent_records]

    denial_dates = [r['date'] for r in denial_records]
    denial_values = [r['value'] for r in denial_records]

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Line plot for Concurrent Records
    ax.plot(concurrent_dates, concurrent_values, label="Concurrent Records (B1)", color="blue", marker="o")

    # Bar plot for Denial Records
    ax.bar(denial_dates, denial_values, label="Denial Records (B2)", color="red", alpha=0.6)

    # Add a horizontal line for the maximum quantity
    ax.axhline(y=quantity, color="green", linestyle="--", linewidth=1.5, label=f"Maximum Quantity ({quantity})")

    # Set plot labels and title
    ax.set_xlabel("Date")
    ax.set_ylabel("Value")
    ax.set_title("Concurrent and Denial Records")
    ax.legend()

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # Display the plot in Streamlit
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
