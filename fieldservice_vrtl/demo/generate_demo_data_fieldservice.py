import random
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from xml.dom import minidom


def generate_demo_data(file_name, start_date, end_date, num_records):
    """
    Generates an XML file with randomized demo data for Odoo.

    Args:
        file_name (str): The name of the XML file to generate.
        start_date (str): The start date for randomization in 'YYYY-MM-DD' format.
        end_date (str): The end date for randomization in 'YYYY-MM-DD' format.
        num_records (int): The number of records to generate.
    """
    # Convert start and end dates to datetime objects
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    # Random descriptions and work instructions
    descriptions = [
        "Routine equipment maintenance.",
        "Safety inspection of machinery.",
        "Calibration of quality control instruments.",
        "Software update for production systems.",
        "Emergency repair of critical equipment.",
        "Scheduled HVAC system maintenance.",
        "Annual fire safety equipment check.",
        "Network infrastructure upgrade.",
        "Pest control treatment for storage areas.",
        "Installation of new production line equipment."
    ]

    work_instructions = [
        "Follow standard operating procedures.",
        "Inspect thoroughly and document findings.",
        "Replace faulty components as needed.",
        "Perform calibration according to guidelines.",
        "Apply safety measures during the task.",
        "Follow software update checklist carefully.",
        "Ensure compliance with fire safety regulations.",
        "Upgrade network switches and test connectivity.",
        "Apply approved pest control chemicals safely.",
        "Assemble and calibrate equipment as per manual."
    ]

    # Create the root <odoo> element
    root = ET.Element("odoo")

    for i in range(1, num_records + 1):
        # Randomize dates within the range
        random_start = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
        random_end = random_start + timedelta(days=random.randint(1, 7))

        # Randomize description and work instructions
        description = random.choice(descriptions)
        work_instruction = random.choice(work_instructions)

        # Create a <record> element
        record = ET.SubElement(root, "record", {
            "id": f"demo_work_order_{i}",
            "model": "fieldservice.order"
        })

        # Add fields to the record
        ET.SubElement(record, "field", {"name": "name"}).text = f"Demo Work Order {i}"
        ET.SubElement(record, "field", {"name": "priority"}).text = str(random.randint(0, 2))
        
        planned_start_datetime = random_start.strftime("%Y-%m-%d %H:%M:%S")
        deadline_datetime = random_end.strftime("%Y-%m-%d %H:%M:%S")
        
        ET.SubElement(record, "field", {"name": "planned_start_datetime"}).text = planned_start_datetime
        ET.SubElement(record, "field", {"name": "deadline_datetime"}).text = deadline_datetime
        
        planned_duration = (random_end - random_start).days * 8  # Assume 8 hours per day
        ET.SubElement(record, "field", {"name": "planned_duration"}).text = str(planned_duration)

        ET.SubElement(record, "field", {"name": "date_start"}).text = random_start.strftime("%Y-%m-%d")
        ET.SubElement(record, "field", {"name": "date_end"}).text = random_end.strftime("%Y-%m-%d")
        
        ET.SubElement(record, "field", {"name": "description"}).text = description
        ET.SubElement(record, "field", {"name": "work_instructions"}).text = work_instruction
        
        location_instruction = f"Location {random.randint(1, 100)}, Room {random.randint(1, 50)}"
        ET.SubElement(record, "field", {"name": "location_instructions"}).text = location_instruction

    # Pretty-print the XML
    xml_string = ET.tostring(root, encoding="unicode")
    dom = minidom.parseString(xml_string)
    pretty_xml_string = dom.toprettyxml(indent="  ")

    # Write the pretty XML to a file
    with open(file_name, 'w') as file:
        file.write(pretty_xml_string)

    print(f"Demo data generated and saved to {file_name}")


# Example usage:
generate_demo_data(
    file_name="/usr/share/odoo-field-service/fieldservice_vrtl/demo/demo_work_orders.xml",
    start_date="2025-04-01",
    end_date="2025-07-31",
    num_records=100
)
