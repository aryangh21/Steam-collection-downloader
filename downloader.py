import requests
import re
import os
import subprocess
import time

# Configuration
WSCOLLECTIONID = 'Your Steam Collection ID'
home = os.path.expanduser("~")
gameid = 'Your game ID';

# Path to steamcmd executable
STEAMCMD_PATH = r"Your SteamCMD path\steamcmd.exe"

# Fetch workshop item IDs from collection
def fetch_workshop_ids(collection_id):
    try:
        response = requests.get(f"https://steamcommunity.com/sharedfiles/filedetails/?id={collection_id}")
        response.raise_for_status()
        workshop_ids = re.findall(r'href="https://steamcommunity.com/sharedfiles/filedetails/\?id=(\d+)"', response.text)
        return workshop_ids[1:]  # Skip the first ID
    except requests.RequestException as e:
        print(f"Error fetching workshop IDs: {e}")
        return []

# Fetch mod name from workshop item ID
def fetch_mod_name(workshop_item):
    try:
        response = requests.get(f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshop_item}")
        response.raise_for_status()
        title_search = re.search(r'<title>(.*?)</title>', response.text)
        if title_search:
            title = title_search.group(1)
            mod_name = ' '.join(title.split()[1:])  # Skip the first word
            return mod_name.strip()
    except requests.RequestException as e:
        print(f"Error fetching mod name for item {workshop_item}: {e}")
    return None

# Sanitize mod name to remove problematic characters
def sanitize_mod_name(mod_name):
    return re.sub(r'[^\w\s-]', '_', mod_name)

# Download and link mods
def download_and_link_mods(workshop_ids, game_id):
    for workshop_item in workshop_ids:
        mod_name = fetch_mod_name(workshop_item)
        if mod_name:
            mod_name_clean = mod_name.replace('\r', '').replace('\n', '')
            mod_name_sanitized = sanitize_mod_name(mod_name_clean)
            print(f"Downloading {mod_name_clean}")
            counter = 1
            while True:
                try:
                    result = subprocess.run([
                        STEAMCMD_PATH, '+login', 'anonymous', '+workshop_download_item', game_id, workshop_item, 'validate', '+quit'
                    ], check=True)
                    break
                except subprocess.CalledProcessError as e:
                    print(f"Error Downloading {mod_name_clean}: {e}. Will try again")
                    counter += 1
                    if counter > 4:
                        print(f"Failed to download {mod_name_clean} after 4 attempts. Exiting.")
                        exit(1)
                    time.sleep(1)  # Add a short delay before retrying

            mod_path = os.path.join(home, ".steam/steamapps/workshop/content/{game_id}", workshop_item)
            mod_link = os.path.join(home, "mods", f"@{mod_name_sanitized}")
            try:
                if not os.path.islink(mod_link):
                    os.symlink(mod_path, mod_link)
            except OSError as e:
                print(f"Error creating symlink for {mod_name_clean}: {e}")

if __name__ == "__main__":
    if WSCOLLECTIONID:
        workshop_ids = fetch_workshop_ids(WSCOLLECTIONID)
        if workshop_ids:
            download_and_link_mods(workshop_ids, gameid)
        else:
            print("No workshop IDs found.")
