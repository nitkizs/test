
# Run
# python image_review_selection.py
import os
import cv2
import xml.etree.ElementTree as ET
from xml.dom import minidom

VALID_EXTS = (".jpg", ".jpeg", ".png",)

IMAGE_FOLDER = r"/home/nithin/Work_Student_Job/dataset/16-04-09_13/to_push/pos/pos_images/"

OUTPUT_XML = os.path.join(IMAGE_FOLDER, "selected_images.xml")


def prettify_xml(element):
    rough_string = ET.tostring(element, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")


def save_xml(selected_images, output_xml):
    root = ET.Element("images")
    unique_images = list(dict.fromkeys(selected_images))

    for img_name in unique_images:
        img_elem = ET.SubElement(root, "image")
        img_elem.set("name", img_name)

    xml_str = prettify_xml(root)

    with open(output_xml, "w", encoding="utf-8") as f:
        f.write(xml_str)

    print(f"[INFO] XML saved to: {output_xml}")
    print(f"[INFO] Total selected images: {len(unique_images)}")


def load_images_from_folder(folder):
    image_files = [
        f for f in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith(VALID_EXTS)
    ]
    image_files.sort()
    return image_files


def fit_image_to_screen(img, max_width=1400, max_height=900):
    h, w = img.shape[:2]
    scale = min(max_width / w, max_height / h, 1.0)
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def draw_overlay(img, img_name, index, total, is_selected, selected_count):
    display = img.copy()

    status = "SELECTED" if is_selected else "NOT SELECTED"
    help_text = "Right: Next | Left: Prev | g: Add | l: Remove | e: Save & Exit"

    cv2.putText(display, f"Index: {index + 1}/{total}", (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.putText(display, f"Status: {status}", (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 255, 0) if is_selected else (0, 0, 255), 2)

    cv2.putText(display, f"Selected: {selected_count}", (20, 135),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)

    cv2.putText(display, help_text, (20, display.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

    return display


def main():
    folder = IMAGE_FOLDER
    output_xml = OUTPUT_XML

    if not os.path.isdir(folder):
        print(f"[ERROR] Folder does not exist: {folder}")
        return

    image_files = load_images_from_folder(folder)

    if not image_files:
        print(f"[ERROR] No images found in folder: {folder}")
        return

    selected_images = []
    selected_set = set()

    index = 0
    total = len(image_files)

    cv2.namedWindow("Image Browser", cv2.WINDOW_NORMAL)

    while True:
        img_name = image_files[index]
        img_path = os.path.join(folder, img_name)

        img = cv2.imread(img_path)
        if img is None:
            print(f"[WARNING] Could not read image: {img_path}")
            if index < total - 1:
                index += 1
                continue
            else:
                print("[INFO] End reached. Saving XML.")
                save_xml(selected_images, output_xml)
                break

        img = fit_image_to_screen(img)
        display = draw_overlay(
            img,
            img_name,
            index,
            total,
            img_name in selected_set,
            len(selected_set)
        )

        cv2.imshow("Image Browser", display)
        key = cv2.waitKeyEx(0)
        print("Pressed key code:", key)

        # Right arrow
        if key in [2555904, 65363, 83]:
            if index < total - 1:
                index += 1
            else:
                print("[INFO] Reached end of images. Saving XML.")
                save_xml(selected_images, output_xml)
                break

        # Left arrow
        elif key in [2424832, 65361, 81]:
            if index > 0:
                index -= 1

        # g -> add
        elif key == ord("g") or key == ord("G"):
            if img_name not in selected_set:
                selected_set.add(img_name)
                selected_images.append(img_name)
                print(f"[INFO] Added: {img_name}")
            else:
                print(f"[INFO] Already selected: {img_name}")

        # l -> remove
        elif key == ord("l") or key == ord("L"):
            if img_name in selected_set:
                selected_set.remove(img_name)
                selected_images.remove(img_name)
                print(f"[INFO] Removed: {img_name}")
            else:
                print(f"[INFO] Not in selection: {img_name}")

        # e -> save and exit
        elif key == ord("e") or key == ord("E"):
            print("[INFO] Saving XML and exiting.")
            save_xml(selected_images, output_xml)
            break

        # ESC
        elif key == 27:
            print("[INFO] ESC pressed. Saving XML.")
            save_xml(selected_images, output_xml)
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()