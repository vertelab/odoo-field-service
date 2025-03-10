import random
import xml.etree.ElementTree as ET
from xml.dom import minidom

def generate_unique_names(num_records):
    """
    Generates a list of unique names by combining first and last names.
    Ensures there are no duplicates.
    """
    first_names = ["John", "Jane", "Michael", "Emily", "David", "Sarah", "Robert", "Lisa", "William", "Emma"]
    last_names = ["Smith", "Johnson", "Brown", "Taylor", "Anderson", "Wilson", "Clark", "Walker", "Wright", "Evans"]

    # Generate all possible combinations of first and last names
    all_names = [f"{first} {last}" for first in first_names for last in last_names]

    # Shuffle the list and return the required number of unique names
    random.shuffle(all_names)
    if num_records > len(all_names):
        raise ValueError("Requested number of records exceeds the number of unique name combinations.")
    
    return all_names[:num_records]

def generate_random_phone():
    return f"+1 {random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"

def generate_random_email(name):
    username = name.lower().replace(" ", ".")
    domains = ["example.com", "testmail.com", "demomail.net", "samplecorp.org"]
    return f"{username}@{random.choice(domains)}"

def generate_demo_data(file_name, num_records):
    """
    Generates an XML file with randomized demo data for Odoo hr.employee model.

    Args:
        file_name (str): The name of the XML file to generate.
        num_records (int): The number of records to generate.
    """
    # Create the root <odoo> element
    root = ET.Element("odoo")

    job_refs = ["hr.job_developer", "hr.job_consultant", "hr.job_hrm", "hr.job_cto", "hr.job_ceo", "hr.	hr.job_marketing", "hr.job_trainer"]

    # Generate unique names
    unique_names = generate_unique_names(num_records)

    for i, name in enumerate(unique_names, start=1):
        # Create a <record> element
        record = ET.SubElement(root, "record", {
            "id": f"test_{i:03d}",
            "model": "hr.employee"
        })

        # Add fields to the record
        ET.SubElement(record, "field", {"name": "name"}).text = name
        ET.SubElement(record, "field", {"name": "private_phone"}).text = generate_random_phone()
        ET.SubElement(record, "field", {"name": "private_email"}).text = generate_random_email(name)
        ET.SubElement(record, "field", {"name": "job_id", "ref": random.choice(job_refs)})

    # Pretty-print the XML
    xml_string = ET.tostring(root, encoding="unicode")
    dom = minidom.parseString(xml_string)
    pretty_xml_string = dom.toprettyxml(indent="  ")

    # Write the pretty XML to a file
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(pretty_xml_string)

    print(f"Demo data generated and saved to {file_name}")

# Example usage:
generate_demo_data(
    file_name="/usr/share/odoo-field-service/fieldservice_vrtl/demo/demo_employees.xml",
    num_records=100
)
