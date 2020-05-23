from PIL import Image
import piexif
from bs4 import BeautifulSoup

from datetime import datetime
from enum import Enum
import json
from pathlib import Path
import os

# relative location of the album folder within the export
ALBUM_PATH: Path = Path("photos_and_videos/album")


class ExportType(Enum):
    UNKNOWN = 0
    HTML = 1
    JSON = 2


def fix_the_date(filename: str, newdate: datetime, targetdir: str):
    """Create a new copy of an image with a given date populated in EXIF

    Args:

        filename: image file to copy

        newdate: new datetime to insert into copy's EXIF metadata

        targetdir: directory to place to newly generated copy in
    """
    Path(targetdir).mkdir(parents=True, exist_ok=True)
    try:
        im = Image.open(filename)
    except IOError:
        print(f"Could not open {filename} - skipping.")
        return

    exif_dict = piexif.load(filename)
    newdate_str = newdate.strftime("%Y:%m:%d %H:%M:%S")
    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = newdate_str
    exif_dict["0th"][piexif.ImageIFD.DateTime] = newdate_str
    exif_bytes = piexif.dump(exif_dict)
    im.save(Path(targetdir) / Path(filename).name, "jpeg", exif=exif_bytes)


def get_album_files(export_dir: str):
    """ Looks for Facebook export albums in export_dir """
    return (Path(export_dir) / ALBUM_PATH).glob("*")


def process_html_album(filename: str):
    """ Process a single exported album .html file """
    text = Path(filename).read_text(encoding="utf8")
    soup = BeautifulSoup(text, "html.parser")
    for image_div in soup.select("div.pam"):
        date_text = image_div.select("div._2lem")[0].text
        date = datetime.strptime(date_text, "%b %d, %Y, %I:%M %p")
        filename = image_div.select("div._2let > a")[0].get("href")
        fix_the_date(filename, date, "test")


def process_json_album(filename: str):
    """ Process a single exported album .json file """
    text = Path(filename).read_text(encoding="utf8")
    parsed_json = json.loads(text)
    for image_data in parsed_json["photos"]:
        filename = image_data["uri"]
        date = datetime.utcfromtimestamp(int(image_data["creation_timestamp"]))
        fix_the_date(filename, date, "test")


def process_all_files(export_dir: str):
    """ Finds all albums and processes every image in each album """

    if not Path(export_dir).exists():
        raise FileNotFoundError(f"{export_dir} not found!")

    os.chdir(export_dir)
    export_type = detect_export_type()
    if export_type is ExportType.UNKNOWN:
        raise Exception("Unrecognized export")

    elif export_type is ExportType.HTML:
        processor = process_html_album

    elif export_type is ExportType.JSON:
        processor = process_json_album

    for file in get_album_files(export_dir):
        print(f"Processing {file}...")
        processor(file)


def detect_export_type() -> ExportType:
    """ Detects if an export is HTML or JSON """
    # album_dir = Path(export_dir) / ALBUM_PATH

    if (ALBUM_PATH / Path("0.html")).exists():
        return ExportType.HTML

    elif (ALBUM_PATH / Path("0.json")).exists():
        return ExportType.JSON

    return ExportType.UNKNOWN


if __name__ == "__main__":
    import sys
    if (len(sys.argv) != 2):
        print("Usage: ./fix-photo-dates.py <export_directory>")
        exit()

    process_all_files(sys.argv[1])
