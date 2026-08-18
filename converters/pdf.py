from pypdf import PdfReader


def pdf_to_text(filepath):
    text = ""

    try:
        reader = PdfReader(filepath)

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    except Exception as e:
        return f"Fehler: {e}"

    return text
