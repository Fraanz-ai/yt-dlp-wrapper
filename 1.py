#!/usr/bin/env python3

import os
import subprocess
import sys
import shutil
import datetime

YT_DLP = "./yt-dlp"

if os.name == "nt":
    YT_DLP += ".exe"

DOWNLOAD_DIR = "downloads"
LOG_FILE = "download_history.txt"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\nPress Enter...")


def header():
    clear()
    print("=" * 55)
    print("        YT-DLP TERMINAL DOWNLOAD MANAGER")
    print("=" * 55)
    print()


def check_binary():
    if not os.path.exists(YT_DLP):
        print("yt-dlp binary not found.")
        print(f"Expected: {YT_DLP}")
        sys.exit(1)

    if shutil.which("ffmpeg"):
        ffmpeg = "Detected"
    else:
        ffmpeg = "Not found"

    print(f"yt-dlp : OK")
    print(f"ffmpeg : {ffmpeg}")
    print()


def log(url, mode):
    with open(LOG_FILE, "a", encoding="utf8") as f:
        t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        f.write(f"{t} | {mode} | {url}\n")


def run(cmd):

    print("\nRunning:\n")
    print(" ".join(cmd))
    print()

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nCancelled.")


def base_cmd(url):

    return [
        "python3",
        YT_DLP,
        url,
        "-P",
        DOWNLOAD_DIR
    ]


def download_video(url):

    cmd = base_cmd(url)

    cmd += [
        "-f",
        "bestvideo+bestaudio/best",
        "--merge-output-format",
        "mp4",
        "--embed-thumbnail",
        "--add-metadata"
    ]

    run(cmd)
    log(url, "VIDEO")


def download_mp3(url):

    cmd = base_cmd(url)

    cmd += [
        "-x",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "0",
        "--embed-thumbnail",
        "--add-metadata"
    ]

    run(cmd)
    log(url, "MP3")


def custom_quality(url):

    print("\n1) 1080p")
    print("2) 720p")
    print("3) 480p")

    q = input("\nChoose: ")

    quality_map = {
        "1": "bestvideo[height<=1080]+bestaudio/best",
        "2": "bestvideo[height<=720]+bestaudio/best",
        "3": "bestvideo[height<=480]+bestaudio/best"
    }

    if q not in quality_map:
        return

    cmd = base_cmd(url)

    cmd += [
        "-f",
        quality_map[q],
        "--merge-output-format",
        "mp4",
        "--embed-thumbnail",
        "--add-metadata"
    ]

    run(cmd)
    log(url, "CUSTOM")


def playlist(url):

    cmd = base_cmd(url)

    cmd += [
        "--yes-playlist",
        "--embed-thumbnail",
        "--add-metadata"
    ]

    run(cmd)
    log(url, "PLAYLIST")


def folder():

    global DOWNLOAD_DIR

    path = input("Folder path: ").strip()

    if not path:
        return

    os.makedirs(path, exist_ok=True)

    DOWNLOAD_DIR = path

    print("Changed.")
    pause()


def menu():

    while True:

        header()
        check_binary()

        print("Download Folder:", DOWNLOAD_DIR)
        print()

        print("1) Download Video (best)")
        print("2) Download MP3")
        print("3) Custom Quality")
        print("4) Download Playlist")
        print("5) Change Download Folder")
        print("6) Exit")

        c = input("\nSelect: ")

        if c == "6":
            break

        if c == "5":
            folder()
            continue

        url = input("\nPaste URL: ").strip()

        if not url:
            continue

        if c == "1":
            download_video(url)

        elif c == "2":
            download_mp3(url)

        elif c == "3":
            custom_quality(url)

        elif c == "4":
            playlist(url)

        pause()


if __name__ == "__main__":
    menu()
