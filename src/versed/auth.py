from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from collections import defaultdict

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate_with_browser():
    """
    Authenticate the user using OAuth 2.0 and return credentials.
    """
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES
    )
    # Run local server for OAuth 2.0 redirect
    creds = flow.run_local_server(port=8080)
    return creds

def fetch_all_files(service):
    """
    Fetch all files and folders from Google Drive.
    """
    print("Fetching all files and folders from your Google Drive...")
    files = []
    page_token = None

    while True:
        response = service.files().list(
            q="'root' in parents or mimeType='application/vnd.google-apps.folder'",
            spaces='drive',
            fields="nextPageToken, files(id, name, mimeType, parents)",
            pageToken=page_token
        ).execute()

        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return files

def build_folder_hierarchy(files):
    """
    Build a folder hierarchy from the list of files.
    """
    hierarchy = defaultdict(list)
    folder_dict = {}

    for file in files:
        if file.get('mimeType') == 'application/vnd.google-apps.folder':
            folder_dict[file['id']] = file['name']

    # Build hierarchy
    for file in files:
        parents = file.get('parents', ['root'])  # Default parent is 'root'
        for parent in parents:
            hierarchy[parent].append(file)

    return hierarchy, folder_dict

def print_hierarchy(hierarchy, folder_dict, parent_id='root', indent=0):
    """
    Recursively print the folder hierarchy.
    """
    if parent_id == 'root':
        print("Root Folder:")
    else:
        print(" " * indent + f"📂 {folder_dict.get(parent_id, 'Unknown Folder')}")

    for file in hierarchy.get(parent_id, []):
        if file.get('mimeType') == 'application/vnd.google-apps.folder':
            print_hierarchy(hierarchy, folder_dict, file['id'], indent + 4)
        else:
            print(" " * (indent + 4) + f"📄 {file['name']}")

def main():
    """
    Main function to authenticate, fetch files, and print the hierarchy.
    """
    credentials = authenticate_with_browser()
    service = build('drive', 'v3', credentials=credentials)

    files = fetch_all_files(service)
    hierarchy, folder_dict = build_folder_hierarchy(files)
    
    print_hierarchy(hierarchy, folder_dict)

if __name__ == "__main__":
    main()
