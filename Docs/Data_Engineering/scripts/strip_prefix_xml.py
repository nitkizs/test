import xml.etree.ElementTree as ET

TARGET_LABEL = "Mavic"
PREFIX_TO_REMOVE = "pos_new/"
INPUT_XML = r"/home/nithin/Work_Student_Job/dataset/16-04-09_13/for_labeling/output/annotations_final_pos_filtered_thrsh-0.07.xml"
OUTPUT_XML = INPUT_XML.replace(".xml", "_final_cleaned.xml")


tree = ET.parse(INPUT_XML)
root = tree.getroot()

images = root.findall("image")
print(f"Total images in original XML: {len(images)}")

new_image_id = 0
images_to_delete = []


for image in images:
    #Fix image name prefix
    name = image.get("name")
    if name and name.startswith(PREFIX_TO_REMOVE):
        name = name.replace(PREFIX_TO_REMOVE, "", 1)
        image.set("name", name)

    #Keep only TARGET_LABEL boxes
    boxes = image.findall("box")
    valid_boxes = [box for box in boxes if box.get("label") == TARGET_LABEL]

    if not valid_boxes:
        images_to_delete.append(image)
        continue

    #Remove non target boxes
    for box in boxes:
        if box.get("label") != TARGET_LABEL:
            image.remove(box)

    #Renumber image ID
    image.set("id", str(new_image_id))
    new_image_id += 1

#Remove images without target label
for image in images_to_delete:
    root.remove(image)

print(f"Removed {len(images_to_delete)} images without '{TARGET_LABEL}' label.")
print(f"Remaining images: {len(images) - len(images_to_delete)}")

tree.write(OUTPUT_XML, encoding="utf-8", xml_declaration=True)
print(f"Final cleaned XML saved as: {OUTPUT_XML}")