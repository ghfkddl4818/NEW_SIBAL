from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGB', (400, 100), color = (255, 255, 255))
d = ImageDraw.Draw(img)

# A simple font might not be available, so this is a fallback.
try:
    font = ImageFont.truetype("arial.ttf", 15)
except IOError:
    font = ImageFont.load_default()

d.text((10,10), "This is a sample product image for testing OCR.", fill=(0,0,0), font=font)
d.text((10,40), "It contains some text and numbers 12345.", fill=(0,0,0), font=font)

img.save("data/product_images/sample.png")
