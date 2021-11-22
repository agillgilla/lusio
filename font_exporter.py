from PIL import Image, ImageFont, ImageDraw
import os

CHARS_TO_EXPORT = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789:"

font = ImageFont.truetype("monospace-typewriter/MonospaceTypewriter.ttf", 72)

EXPORT_DIR = "font_imgs"

def get_char_bounding_box(char):
	image = Image.new("RGB", (800, 600))

	draw = ImageDraw.Draw(image)
	draw.text((0, 0), char, font=font, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(255, 255, 255, 255))

	return image.getbbox()

def get_max_bounding_box():
	max_box = (float("inf"), float("inf"), float("-inf"), float("-inf"))
	for char in CHARS_TO_EXPORT:
		curr_box = get_char_bounding_box(char)
		max_box = (min(max_box[0], curr_box[0]), min(max_box[1], curr_box[1]), max(max_box[2], curr_box[2]), max(max_box[3], curr_box[3]))
	return max_box

def export_char_img(char, box):
	image = Image.new("RGB", (800, 600))

	draw = ImageDraw.Draw(image)

	draw.rectangle([(0,0), image.size], fill=(0, 255, 0))
	#draw.rectangle([(0,0), (5, 5)], fill=(0, 255, 0))
	draw.text((0, 0), char, font=font, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 255))

	image = image.crop(box)

	if char.islower():
		image.save(os.path.join(EXPORT_DIR, f"_{char}.bmp"))
	elif char == ":":
		image.save(os.path.join(EXPORT_DIR, f"colon.bmp"))
	else:
		image.save(os.path.join(EXPORT_DIR, f"{char}.bmp"))

if not os.path.exists(EXPORT_DIR):
	os.makedirs(EXPORT_DIR)

char_img_box = get_max_bounding_box()

for char in CHARS_TO_EXPORT:
	export_char_img(char, char_img_box)