import subprocess
import shlex
import os
import re
import requests
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC, APIC, error


# --- Tagging Helper Functions (from your second script) ---
def clean_filename(filename):
    """
    Strips out common junk from downloaded MP3 file names to improve search accuracy.
    """
    # Remove file extension
    name = os.path.splitext(filename)[0]
    
    # Remove anything inside parentheses () or brackets []
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'\[.*?\]', '', name)
    
    # Remove common extra fluff words
    fluff_words = ['official', 'video', 'audio', 'lyric', 'lyrics', 'hq', 'hd', 'remastered', 'kbps']
    for word in fluff_words:
        name = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE).sub('', name)
        
    # Clean up leftover spaces or dashes
    name = re.sub(r'\s+', ' ', name).strip('- ')
    
    return name


def fetch_metadata(query):
    """
    Searches the iTunes API for the song and returns the metadata and album art URL.
    """
    url = f"https://itunes.apple.com/search?term={query}&media=music&entity=song&limit=1"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data['resultCount'] > 0:
            result = data['results'][0]
            
            # iTunes returns 100x100 art by default. Replace to get 600x600.
            art_url = result.get('artworkUrl100', '').replace('100x100bb', '600x600bb')
            
            return {
                'title': result.get('trackName', ''),
                'artist': result.get('artistName', ''),
                'album': result.get('collectionName', ''),
                'genre': result.get('primaryGenreName', ''),
                'year': result.get('releaseDate', '')[:4],  # Just the YYYY
                'art_url': art_url
            }
    except requests.exceptions.RequestException as e:
        print(f"Network error searching for '{query}': {e}")
    except ValueError:
        print(f"Failed to parse data for '{query}'")
        
    return None


def tag_mp3(filepath, metadata):
    """
    Embeds the fetched metadata and album art into the MP3 file using Mutagen.
    """
    try:
        audio = MP3(filepath, ID3=ID3)
        
        # Add an ID3 tag header if the file completely lacks one
        try:
            audio.add_tags()
        except error:
            pass  # Tags already exist
            
        if metadata['title']:
            audio.tags.add(TIT2(encoding=3, text=metadata['title']))
        if metadata['artist']:
            audio.tags.add(TPE1(encoding=3, text=metadata['artist']))
        if metadata['album']:
            audio.tags.add(TALB(encoding=3, text=metadata['album']))
        if metadata['genre']:
            audio.tags.add(TCON(encoding=3, text=metadata['genre']))
        if metadata['year']:
            audio.tags.add(TDRC(encoding=3, text=metadata['year']))

        # Fetch and embed the Album Art
        if metadata['art_url']:
            img_response = requests.get(metadata['art_url'])
            if img_response.status_code == 200:
                audio.tags.add(
                    APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,        # Front Cover
                        desc=u'Cover',
                        data=img_response.content
                    )
                )

        audio.save()
        print(f"✅ Success: {metadata['title']} by {metadata['artist']}")
        
    except Exception as e:
        print(f"❌ Error tagging file {os.path.basename(filepath)}: {e}")


# --- Main download function, now with tagging ---
def download_video(link, quality_limit, audio_only=False):
    """Downloads a video/audio and, if it's audio, tags it with metadata."""
    try:
        command = ["python3", "yt-dlp"]
        command.extend(["-P", "./downloads"]) 
        # Prepare the base command for audio or video
        if audio_only:
            # --print after_move:filepath outputs the final file path when the download finishes
            command.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0", "--print", "after_move:filepath"])
        elif quality_limit:
            command.extend(shlex.split(quality_limit))

        command.append(link)

        print(f"\n▶️  Starting download for: {link}")
        
        # Run yt-dlp and capture the output so we can get the file path
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ yt-dlp error (exit code {result.returncode}):")
            print(result.stderr)
            return
        
        # Extract the downloaded file path from stdout (last non‑empty line)
        output_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        file_path = output_lines[-1] if output_lines else None
        
        if audio_only and file_path and os.path.exists(file_path):
            # Tag the newly downloaded MP3
            search_query = clean_filename(os.path.basename(file_path))
            if search_query:
                metadata = fetch_metadata(search_query)
                if metadata:
                    tag_mp3(file_path, metadata)
                else:
                    print(f"⚠️ Not Found: Could not find online data for '{search_query}'")
            else:
                print(f"⚠️ Skipped tagging: Couldn't generate a search query from the filename.")
        else:
            if not audio_only:
                print("✅ Video download finished (no tagging needed).")
            else:
                print("⚠️ Could not locate the downloaded MP3 file for tagging.")
                
    except FileNotFoundError:
        print(f"❌ Error: The 'yt-dlp' file was not found.")
        print("    Please make sure the 'yt-dlp' executable file is in the same directory as this script.")
    except Exception as e:
        print(f"❌ An unexpected error occurred while downloading {link}: {e}")


def main():
    quality_limit = "-f 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'"

    while True:
        prompt = ("\nEnter YouTube link(s) or choose an option:\n"
                  "  'l' - to enter a list of links\n"
                  "  'b' - for best available quality (removes 1080p limit for video)\n"
                  "  'm' - to download audio as MP3 (and tag it)\n"
                  "  'q' - to quit\n"
                  "➡️  ")
        link_input = input(prompt).strip()

        if link_input.lower() == 'q':
            print("\nExiting...")
            break

        elif link_input.lower() == 'b':
            quality_limit = ""
            print("\n⚙️  Quality limit removed for video downloads.")
            continue

        elif link_input.lower() == 'm':
            print("\n🎧  MP3 audio download mode enabled. Files will be tagged automatically.")
            print("    (Enter 'v' to switch back to video mode, or 'q' to quit)")

            while True:
                link_input_audio = input("➡️  ").strip()
                if link_input_audio.lower() == 'q':
                    print("\nExiting...")
                    return
                elif link_input_audio.lower() == 'v':
                    print("\n▶️  Video download mode enabled.")
                    break
                elif link_input_audio:
                    download_video(link_input_audio, quality_limit, audio_only=True)
                else:
                    print("Invalid input. Please enter a link, 'v' to switch, or 'q' to quit.")

        elif link_input.lower() == 'l':
            print("\nEnter all YouTube links separated by spaces, then press Enter.")
            links_str = input("➡️  ").strip()
            if not links_str:
                print("No links provided.")
                continue

            links = links_str.split()
            total = len(links)
            print(f"\nFound {total} links. Starting batch download...")
            for i, link in enumerate(links, 1):
                print(f"\n--- Downloading video {i} of {total} ---")
                download_video(link, quality_limit)
            print("\n🎉 Batch download complete!")

        elif link_input:
            download_video(link_input, quality_limit)

        else:
            print("Invalid input. Please try again.")


if __name__ == "__main__":
    main()
    
