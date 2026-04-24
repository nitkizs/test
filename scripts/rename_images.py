# Expects a root folder containing subfolders of images
import os
from tqdm import tqdm

PREFIX = "dd16" # Change 
DATE = "26-04-10" # Change 

def rename_images(root_dir):
    global inval_img
    global img_renamed

    for folder_name in os.listdir(root_dir):

        folder_path = os.path.join(root_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        img_renamed = 0
        
        print(f"Processing: {folder_name}")

        files = sorted(os.listdir(folder_path))

        for file_name in tqdm(files, desc=f"Processing {folder_name}"):

            file_path = os.path.join(folder_path, file_name)
            base, ext = os.path.splitext(file_name)
            try:
                seq = base.split("_")[-1]
                new_name = f"{PREFIX}_{DATE}_{folder_name}_{seq}{ext}"
                new_path = os.path.join(folder_path, new_name)
                os.rename(file_path, new_path)
                img_renamed += 1
            except IndexError:
                inval_img += 1
                continue
        print(f"Folder {folder_name} completed → Renamed {img_renamed} images")

if __name__ == "__main__":
    root_directory = r""
    inval_img = 0
    img_renamed = 0
    rename_images(root_directory)
    if inval_img == 0:
        print(f"All files are renamed without any issue")
    else:
        print(f"{inval_img} images are invalid")