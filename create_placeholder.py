from PIL import Image, ImageDraw, ImageFont
import os

# Create a new image with a light gray background
width = 800
height = 600
color = (240, 240, 240)
img = Image.new('RGB', (width, height), color)

# Get a drawing context
draw = ImageDraw.Draw(img)

# Draw text
text = "No Image Available"
text_color = (128, 128, 128)

# Calculate text position to center it
text_bbox = draw.textbbox((0, 0), text)
text_width = text_bbox[2] - text_bbox[0]
text_height = text_bbox[3] - text_bbox[1]

x = (width - text_width) // 2
y = (height - text_height) // 2

# Draw the text
draw.text((x, y), text, fill=text_color)

# Ensure the directory exists
os.makedirs('static/img', exist_ok=True)

# Save the image
img.save('static/img/news-placeholder.jpg', 'JPEG')
print("Placeholder image created successfully!") 