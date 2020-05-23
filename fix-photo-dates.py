from PIL import Image
import piexif
from bs4 import BeautifulSoup

from datetime import datetime
from pathlib import Path


def fix_the_date(filename: str, newdate: datetime, targetdir: str):
    """Create a new copy of an image with a given date populated in EXIF

    Args:

        filename: image file to copy

        newdate: new datetime to insert into copy's EXIF metadata

        targetdir: export_dirctory to place to newly generated copy in
    """
    Path(targetdir).mkdir(parents=True, exist_ok=True)
    im = Image.open(filename)
    exif_dict = piexif.load(filename)
    newdate_str = newdate.strftime("%Y:%m:%d %H:%M:%S")
    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = newdate_str
    exif_dict["0th"][piexif.ImageIFD.DateTime] = newdate_str
    exif_bytes = piexif.dump(exif_dict)
    im.save(Path(targetdir) / Path(filename).name, "jpeg", exif=exif_bytes)


def get_album_files(export_dir: str):
    """ Looks for Facebook export albums in a export_dirctory """
    return (Path(export_dir) / Path("photos_and_videos/album")).glob("*.html")


def process_html_album(filename: str):
    """ Process a single exported album .html file """
    print(f"Processing {filename}...")
    text = Path(filename).read_text(encoding="utf8")
    soup = BeautifulSoup(text, "html.parser")
    for image_div in soup.select("div.pam"):
        date_text = image_div.select("div._2lem")[0].text
        date = datetime.strptime(date_text, "%b %d, %Y, %I:%M %p")
        filename = image_div.select("div._2let > a")[0].get("href")
        fix_the_date(filename, date, "test")


def process_all_files(export_dir: str):
    """ Finds all albums and processes every image in each album """
    for file in get_album_files(export_dir):
        process_html_album(file)


process_all_files(".")
