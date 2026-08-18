from PIL import Image
import pytesseract


def convert(path):
    image = Image.open(path)

    return pytesseract.image_to_string(image)