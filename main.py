import requests
from requests.exceptions import HTTPError

from time import time as timer

import secrets
import json
import os
import re

from mime_types_ext import mime_types_ext

ONE_KB = 1024  # 1KB = 1024B


# TODO!
# Need to find a better way to get file name and (at least) file extension
# from request/response header; currently I'm using Content-Disposition
# and Content-Type (MIME) from HTTP header with a help from secret module
# to generate random file name. This is not ideal (Content-Disposition
# may not be present in a header) and there's way to many different MIME
# types available to handle them all by using mime_types_ext dictionary

# MAYBE: try to get file name and extension from URL (if possible)

# TODO!
# Add multithreading - each file can be downloaded in a separated thread

# TODO!
# Add graphical user interface (PyQt ?)

# TODO!
# Add error handling


# load JSON file that contains list of files to download
def load_files_list(path):
    path = os.path.expanduser(path)
    if os.path.exists(path):
        with open(path, "r") as file:
            return json.loads(file.read())


# get file extension from Content-Disposition or Mime-Type
# generate random file name
def get_file_name(content_disposition, mime_type):
    #print(f"Content-Disposition: {content_disposition}")
    #print(f"Mime-Type: {mime_type}")

    filename = secrets.token_urlsafe(10)

    # if Content-Disposition is available in header
    # try to get file extension from filename
    if content_disposition:
        fname = re.findall(
            r"filename=\"(.+)\"", content_disposition, flags=re.IGNORECASE)
        if fname:
            # dot_index = fname[0].rfind(".")
            # if dot_index != -1:
            #     extension = fname[dot_index:]
            #     return f"{filename}{extension}"
            return re.sub(r"\s+", "_", fname[0])

    # use Mime-Type from header to figure out file extension
    if mime_type:
        mime_ext = list(
            filter(lambda mtype: mtype[0] in mime_type.lower(), mime_types_ext))
        if mime_ext:
            (mime_type, extension) = mime_ext[0]
            return f"{filename}{extension}"

    return filename


# creates directory for downloaded files (if needed)
# returns path to the new downloaded file
def get_filepath(filename):
    folder = f"{os.getcwd()}{os.sep}downloaded"

    if not os.path.exists(folder):
        os.makedirs(folder)

    return f"{folder}{os.sep}{filename}"


# gets size in B, KB or MB
def get_resource_size(bytes):
    if bytes:
        kb = round(bytes / ONE_KB, 1)
        if kb < ONE_KB:
            return f"{kb} KB"

        mb = round(kb / ONE_KB, 1)
        if mb > 0.1:
            return f"{mb} MB"

        return f"{bytes} B"


# downloads file with given url
def download_file(url):
    try:
        with requests.get(url, stream=True) as req:
            req.raise_for_status()

            # print(req.headers)
            resource_size = get_resource_size(
                int(req.headers.get("Content-Length", 0)))

            filename = get_file_name(req.headers.get(
                "Content-Disposition", None), req.headers.get("Content-Type", None))

            if filename:
                filepath = get_filepath(filename)

                with open(filepath, "wb") as file:
                    for chunk in req.iter_content(chunk_size=1*1024):
                        if chunk:
                            file.write(chunk)

                return {
                    "filepath": filepath,
                    "size": resource_size,
                    "bytes": int(req.headers.get("Content-Length", 0)),
                    "url": url
                }
    except HTTPError as http_error:
        print(f"HTTP Error occured: {http_error}")
    except Exception as error:
        print(error)


# download all files from JSON file
def download_all_files(filelist):
    urls_list = f"{os.getcwd()}{os.sep}{filelist}"
    urls = load_files_list(path=urls_list)

    start = timer()

    num_of_files_downloaded = 0
    total_bytes_downloaded = 0

    for index, url in enumerate(urls):
        dl_info = download_file(url)
        if dl_info:
            num_of_files_downloaded += 1
            total_bytes_downloaded += dl_info.get("bytes", 0)

            print(
                f"FILE ({str(index + 1).zfill(3)}): {dl_info.get('filepath', '???')}, " +
                f"SIZE: {dl_info.get('size', '???')}, URL: {dl_info['url']}")

    print("*** ALL DONE ***")
    print(f"Downloaded {num_of_files_downloaded} file(s)")
    print(f"Total: {get_resource_size(total_bytes_downloaded)}")

    print(f"Elapsed time: {timer() - start}")


if __name__ == "__main__":
    download_all_files("files_to_download.json")
