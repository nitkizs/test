import os
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image


def create_cvat_xml(image_dir, output_xml):
    annotations_root = ET.Element("annotations")

    image_list = sorted(os.listdir(image_dir))
    selected_images = [
        img for img in image_list
        if img.lower().endswith(('.png','.jpg'))
    ]

    for idx, image_name in enumerate(selected_images):
        image_path = os.path.join(image_dir, image_name)
        with Image.open(image_path) as img:
            width, height = img.size

        ET.SubElement(
            annotations_root,
            "image",
            id=str(idx),
            name=os.path.splitext(image_name)[0] + ".png",  
            width=str(width),
            height=str(height)
        )

    def pretty_write(element, file, indent=" ", level=0):
        if len(element):
            file.write(f"{indent * level}<{element.tag} {format_attrib(element.attrib)}>\n")
            for child in element:
                pretty_write(child, file, indent, level + 1)
            file.write(f"{indent * level}</{element.tag}>\n")
        else:
            file.write(f"{indent * level}<{element.tag} {format_attrib(element.attrib)} />\n")

    def format_attrib(attrib):
        return ' '.join(f'{key}="{value}"' for key, value in attrib.items())

    with open(output_xml, 'w', encoding='utf-8') as f:
        f.write("<?xml version='1.0' encoding='utf-8'?>\n")
        pretty_write(annotations_root, f)


if __name__ == "__main__":
    image_folder = r""
    image_directory = Path(image_folder)
    output_xml = image_directory.parent / ("annotations_" + image_directory.name + ".xml")
    create_cvat_xml(image_directory, output_xml)
    print(f"Created XML in {image_directory.parent}")

