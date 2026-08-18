from PIL import Image

try:
    import pytesseract

    OCR_ENABLED = True

except Exception:
    OCR_ENABLED = False


def image_to_text(filepath):
    try:
        image = Image.open(filepath)

        # GIF: erstes Bild verwenden
        if getattr(image, "is_animated", False):
            image.seek(0)

        image.load()

        information = [
            f"Datei: {filepath}",
            f"Format: {image.format}",
            f"Größe: {image.width} x {image.height}"
        ]

        if OCR_ENABLED:
            try:
                text = pytesseract.image_to_string(image)

                if text.strip():
                    information.append("")
                    information.append("OCR-Text:")
                    information.append(text)

            except Exception as error:
                information.append("")
                information.append(
                    f"OCR nicht verfügbar: {error}"
                )

        return "\n".join(information)

    except Exception as error:
        return f"Bild konnte nicht verarbeitet werden: {error}"
