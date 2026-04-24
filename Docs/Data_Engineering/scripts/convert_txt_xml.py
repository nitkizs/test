import glob
from pathlib import Path
import xml.etree.ElementTree as ET

imgs = r"/home/Yolo-FV2/output/exp-22/labels/"
out_xml = r"/home/dataset/flug-01_26-04-09//Overcast-with-sun.xml"
shrink_val = 3 
IMG_W, IMG_H = 1024, 768
LABEL_NAME = "Mavic"   
IMG_EXT = ".png"        
TOP_N = 5  

root_out = ET.Element("annotations")
label_files = sorted(Path(imgs).glob("*.txt"))

for i, label_file in enumerate(label_files):
    image_el = ET.Element("image")
    image_el.set("id", str(i))
    image_el.set("name", label_file.with_suffix(IMG_EXT).name)
    image_el.set("width", str(IMG_W))
    image_el.set("height", str(IMG_H))

    detections = []
    with open(label_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            # class_id, xc, yc, bw, bh, confidence
            if len(parts) >= 5:
                conf = float(parts[5]) if len(parts) > 5 else 0.0
                detections.append({'parts': parts, 'conf': conf})

    # top "n" CONF dets
    if detections:
        # Sort-conf descending
        sorted_detections = sorted(detections, key=lambda x: x['conf'], reverse=True)
        
        # top N dets
        top_n_detections = sorted_detections[:TOP_N]

        for detection in top_n_detections:
            parts = detection['parts']

            # YOLO (normalized) to abs Pixels
            xc, yc, bw, bh = map(float, parts[1:5])
            
            xtl = (xc - bw / 2.0) * IMG_W
            ytl = (yc - bh / 2.0) * IMG_H
            xbr = (xc + bw / 2.0) * IMG_W
            ybr = (yc + bh / 2.0) * IMG_H

            # shrink
            xtl_s = xtl + shrink_val
            ytl_s = ytl + shrink_val
            xbr_s = xbr - shrink_val
            ybr_s = ybr - shrink_val

            # clipping
            if xbr_s > xtl_s and ybr_s > ytl_s:
                xtl_s = max(0, min(IMG_W, xtl_s))
                ytl_s = max(0, min(IMG_H, ytl_s))
                xbr_s = max(0, min(IMG_W, xbr_s))
                ybr_s = max(0, min(IMG_H, ybr_s))

                ET.SubElement(
                    image_el, "box", label=LABEL_NAME, occluded="0", source="manual",
                    xtl=f"{xtl_s:.2f}", ytl=f"{ytl_s:.2f}", 
                    xbr=f"{xbr_s:.2f}", ybr=f"{ybr_s:.2f}",
                    z_order="0")

    root_out.append(image_el)

tree_out = ET.ElementTree(root_out)
if hasattr(ET, "indent"):
    ET.indent(tree_out, space="  ")
    
tree_out.write(out_xml, encoding="utf-8", xml_declaration=True)
print(f"Wrote: {out_xml} ({len(label_files)} images, kept top {TOP_N} detections per image)")