import xml.etree.ElementTree as ET
from datetime import datetime

base_xml = r"/home/old_annotations.xml"
new_xml = r"/home/new_annotations.xml"
merged_xml = r"/home/merged_annotations.xml"

base_tree = ET.parse(base_xml)
base_root = base_tree.getroot()

new_tree = ET.parse(new_xml)
new_root = new_tree.getroot()

base_images = base_root.findall("image")
new_images = new_root.findall("image")

# Update image IDs and append
counter = len(base_images)
for image in new_images:
    image.set("id", str(counter))
    base_root.append(image)
    counter += 1

# Update <meta> 
meta = base_root.find("meta")
if meta is not None:
    task = meta.find("task")
    if task is not None:
        now_time = datetime.now().isoformat(timespec="seconds")

        total_images = len(base_root.findall("image"))

        # Update updated time
        updated = task.find("updated")
        if updated is not None:
            updated.text = now_time

        # Update size
        size = task.find("size")
        if size is not None:
            size.text = str(total_images)
            size = task.find("size")


        # Update start_frame
        start_frame = task.find("start_frame")
        if start_frame is not None:
            start_frame.text = "0"

        # Update stop_frame
        stop_frame = task.find("stop_frame")
        if stop_frame is not None:
            stop_frame.text = str(total_images - 1)

        # Update segment start/stop
        segment = task.find("./segments/segment")
        if segment is not None:
            seg_start = segment.find("start")
            seg_stop = segment.find("stop")

            if seg_start is not None:
                seg_start.text = "0"
            if seg_stop is not None:
                seg_stop.text = str(total_images - 1)
    else:
        if meta is not None:
             # Check if size exists
            size = meta.find("size")
            if size is None:
                size = ET.SubElement(meta, "size")
            # Count total images
            total_images = len(base_root.findall("image"))
            size.text = str(total_images)


base_tree.write(merged_xml, encoding="utf-8", xml_declaration=True)
print(f"Merged XML saved to: {merged_xml}")

