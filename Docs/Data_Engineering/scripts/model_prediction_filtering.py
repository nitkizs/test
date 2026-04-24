import os
import shutil
import xml.etree.ElementTree as ET
from xml.dom import minidom

input_folder = r""
confidence_threshold = 0.7

# Output folders
empty_folder = os.path.join(input_folder, "no_detections")
low_conf_folder = os.path.join(input_folder, "low_confidence")
high_conf_folder = os.path.join(input_folder, "high_confidence")
multi_mixed_folder = os.path.join(input_folder, "multiple_mixed_confidence")
multi_high_folder = os.path.join(input_folder, "multiple_high_confidence")

# Create folders
for folder in [empty_folder, low_conf_folder, high_conf_folder, multi_mixed_folder, multi_high_folder]:
    os.makedirs(folder, exist_ok=True)

# Process each txt file
for txt_file in os.listdir(input_folder):
    if not txt_file.endswith(".txt"):
        continue

    txt_path = os.path.join(input_folder, txt_file)

    with open(txt_path, "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    # No detections
    if len(lines) == 0:
        shutil.move(txt_path, os.path.join(empty_folder, txt_file))

    # Multiple detections
    elif len(lines) > 1:
        confidences = []

        for line in lines:
            parts = line.split()
            if len(parts) != 6:
                continue
            confidences.append(float(parts[5]))

        if any(conf <= confidence_threshold for conf in confidences):
            shutil.move(txt_path, os.path.join(multi_mixed_folder, txt_file))
        else:
            shutil.move(txt_path, os.path.join(multi_high_folder, txt_file))

    # Single detection
    else:
        parts = lines[0].split()
        if len(parts) != 6:
            print(f"Skipping {txt_file}, unexpected format")
            continue

        confidence = float(parts[5])

        if confidence <= confidence_threshold:
            shutil.move(txt_path, os.path.join(low_conf_folder, txt_file))
        else:
            shutil.move(txt_path, os.path.join(high_conf_folder, txt_file))


for root_dir, dirs, files in os.walk(input_folder):
    txt_files = sorted([f for f in files if f.endswith(".txt")])

    if txt_files:
        root = ET.Element("annotations")

        for idx, file_name in enumerate(txt_files):
            png_name = file_name.replace(".txt", ".png")

            img_element = ET.SubElement(root, "image")
            img_element.set("id", str(idx))
            img_element.set("name", png_name)

        xml_str = ET.tostring(root, encoding='utf-8')
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="    ")

        parent_folder_name = os.path.basename(root_dir)
        xml_output_path = os.path.join(root_dir, parent_folder_name + ".xml")

        with open(xml_output_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml)

        print(f"XML file created: {xml_output_path}")