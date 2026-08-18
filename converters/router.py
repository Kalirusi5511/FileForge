from pathlib import Path

from converters import image
from converters import office
from converters import pdf
from converters import text


class ConverterRouter:

    TEXT_EXTENSIONS = {
        ".txt",
        ".md",
        ".py",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".csv",
        ".html",
        ".css",
        ".js",
    }

    IMAGE_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".bmp",
        ".gif",
        ".tiff",
        ".webp",
    }

    OFFICE_EXTENSIONS = {
        ".docx",
        ".xlsx",
    }

    SUPPORTED_FORMATS = (
        TEXT_EXTENSIONS
        | IMAGE_EXTENSIONS
        | OFFICE_EXTENSIONS
        | {".pdf"}
    )

    def can_convert(self, filename):

        return (
            Path(filename).suffix.lower()
            in self.SUPPORTED_FORMATS
        )

    def convert(self, file_path, output_path):

        extension = Path(file_path).suffix.lower()

        if extension == ".pdf":
            content = pdf.convert(file_path)

        elif extension == ".docx":
            content = office.docx_to_text(file_path)

        elif extension == ".xlsx":
            content = office.xlsx_to_text(file_path)

        elif extension in self.IMAGE_EXTENSIONS:
            content = image.convert(file_path)

        elif extension in text.TEXT_EXTENSIONS:
            content = text.convert(file_path)

        else:
            return False

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True