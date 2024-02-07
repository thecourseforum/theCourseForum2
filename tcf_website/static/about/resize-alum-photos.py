import os

from PIL import Image

folders = [
    "tcf_website/static/about/team-pfps",
    "tcf_website/static/about/alum-pfps",
]

eight_hundred_images_alum = []
resizable_images_alum = []

eight_hundred_images_team = []
resizable_images_team = []

for folder_path in folders:
    folder_name = os.path.basename(folder_path)
    for filename in os.listdir(folder_path):
        image_path = os.path.join(folder_path, filename)
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                dimensions = f"{width}x{height}"
                if width == 800 and height == 800:
                    if folder_name == "alum-pfps":
                        eight_hundred_images_alum.append((filename, dimensions))
                    elif folder_name == "team-pfps":
                        eight_hundred_images_team.append((filename, dimensions))
                elif width > 800 or height > 800:
                    if folder_name == "alum-pfps":
                        resizable_images_alum.append((filename, dimensions))
                    elif folder_name == "team-pfps":
                        resizable_images_team.append((filename, dimensions))
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")

print("alum-pfps")

print("Images that are 800x800:")
for filename, dimensions in eight_hundred_images_alum:
    print(f"    {filename} ({dimensions})")

print("Images that are not 800x800 but are resizable:")
for filename, dimensions in resizable_images_alum:
    print(f"    {filename} ({dimensions})")
print("----------------------------------------")

print("team-pfps")
print("Images that are 800x800:")
for filename, dimensions in eight_hundred_images_team:
    print(f"    {filename} ({dimensions})")

print("Images that are not 800x800 but are resizable:")
for filename, dimensions in resizable_images_team:
    print(f"    {filename} ({dimensions})")

for folder_name, images in [
    ("alum-pfps", resizable_images_alum),
    ("team-pfps", resizable_images_team),
]:
    print(f"Resizing images in {folder_name} folder:")
    for filename, dimensions in images:
        user_input = input(
            f"Do you want to resize {filename} ({dimensions}) to 800x800? (Y/N): "
        )
        if user_input.lower() == "y":
            with Image.open(
                f"tcf_website/static/about/{folder_name}/{filename}"
            ) as img:
                img = img.resize((800, 800), Image.ANTIALIAS)
                img.save(
                    os.path.join(
                        f"tcf_website/static/about/{folder_name}/{filename}"
                    )
                )
            print(f"{filename} resized to 800x800")
        else:
            print(f"{filename} not resized")
