import os
import shutil

src_dir = r"dataset/26-04-13/flug-02/"
file_path = r"dataset/26-04-13/flug-02_postive_images.txt"

positive_dir = os.path.join(src_dir, "positive_images")
negative_dir = os.path.join(src_dir, "negative_images")

os.makedirs(positive_dir, exist_ok=True)
os.makedirs(negative_dir, exist_ok=True)

ranges = []
with open(file_path, "r") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            start, end = map(int, line.split("-"))
            ranges.append((start, end))
        except ValueError:
            print(f"Skipping invalid line: {line}")

range_counts = {r: 0 for r in ranges}

positive_count = 0
negative_count = 0

for fname in os.listdir(src_dir):
    src_path = os.path.join(src_dir, fname)

    if not os.path.isfile(src_path):
        continue

    if not fname.lower().endswith(".png"):
        continue

    try:
        num = int(fname.split("_")[-1].replace(".png", ""))
    except ValueError:
        continue

    moved = False

    for r in ranges:
        start, end = r
        if start <= num <= end:
            dst_path = os.path.join(positive_dir, fname)
            shutil.move(src_path, dst_path)
            range_counts[r] += 1
            positive_count += 1
            moved = True
            break

    if not moved:
        dst_path = os.path.join(negative_dir, fname)
        shutil.move(src_path, dst_path)
        negative_count += 1

for (start, end), count in range_counts.items():
    print(f"{start}-{end} → {count} images moved to positive folder")

print(f"Total positive images: {positive_count}")
print(f"Total negative images: {negative_count}")
print("Done")