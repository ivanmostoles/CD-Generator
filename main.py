import streamlit as st
import random
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

# Placeholder for generating XML content
def generate_concurrent_xml(records):
    """
    Generates XML content for concurrent usage records (B1).
    :param records: List of concurrent records with associated data.
    :return: XML Element Tree as a string.
    """
    root = ET.Element("ConcurrentRecords")
    for record in records:
        entry = ET.SubElement(root, "Record")
        ET.SubElement(entry, "Date").text = record['date']
        ET.SubElement(entry, "Value").text = str(record['value'])
    return ET.tostring(root, encoding='utf-8', method='xml').decode()


def generate_denial_xml(records):
    """
    Generates XML content for denial records (B2).
    :param records: List of denial records with associated data.
    :return: XML Element Tree as a string.
    """
    root = ET.Element("DenialRecords")
    for record in records:
        entry = ET.SubElement(root, "Record")
        ET.SubElement(entry, "Date").text = record['date']
        ET.SubElement(entry, "Value").text = str(record['value'])
    return ET.tostring(root, encoding='utf-8', method='xml').decode()


# Streamlit app
st.title("Concurrent and Denial Record Generator")

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
    overpeak_count = random.randint(range_start, range_end)
    original_overpeak_count = overpeak_count  # Track original overpeak count
    phase = "increment"  # Start with the increment phase
    median_reached = False
    double_decrement_next = False  # For even overpeak records

    while current_date <= end_date:
        if phase == "increment" and value < quantity:
            # Incremental records (B1)
            records.append({"date": current_date.strftime("%Y-%m-%d"), "value": value, "type": "B1"})
            value += increment_value
        elif phase == "denial" and overpeak_count > 0:
            # Denial records (B2)
            records.append({"date": current_date.strftime("%Y-%m-%d"), "value": value, "type": "B2"})
            overpeak_count -= 1

            # Determine the median
            if not median_reached:
                if overpeak_count == (original_overpeak_count // 2) - 1:  # Second median for even counts
                    median_reached = True
                    double_decrement_next = True  # Apply double decrement next
                elif overpeak_count == (original_overpeak_count // 2):  # Single median for odd counts
                    median_reached = True

            # Increment or prepare for decrement
            if not median_reached:
                value += increment_value  # Continue incrementing
            else:
                if double_decrement_next:  # Apply double decrement after second median
                    value -= 2 * increment_value
                    double_decrement_next = False  # Reset after one double decrement
                else:
                    value -= increment_value  # Regular decrement
        elif phase == "decrement":
            # Decremental records (B1)
            records.append({"date": current_date.strftime("%Y-%m-%d"), "value": value, "type": "B1"})

            if value <= quantity / 2:  # Stop decrementing at half-threshold
                phase = "increment"
                value += increment_value  # Increment back up from the last valid record
            else:
                value -= increment_value  # Regular decrement
        else:
            # Move to the next phase
            if phase == "increment" and value >= quantity:
                phase = "denial"
            elif phase == "denial" and overpeak_count <= 0:
                phase = "decrement"

            # Reset flags for the next cycle
            if phase == "increment":
                median_reached = False
                double_decrement_next = False

        # Increment date
        current_date += timedelta(days=1)

    # Generate XML files and store them in session state
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



