import os

from dotenv import load_dotenv
from apiclient import discovery
from google.oauth2 import service_account

load_dotenv()

developer_gmail_list = [
    "mohsin.anees@iblinknext.com",
    "muneeb.mashhood@iblinknext.com",
    "aasim.alkayani@iblinknext.com",
]

scopes = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets"
]
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"

class GoogleUtils:

    def __init__(self, enforce_production_p=False, google_drive_folder=None, master_reset=False):
        # read environment variables
        mock_google_api = os.getenv('MOCK_GOOGLE_API')
        credentials_filepath = os.getenv('GOOGLE_CREDENTIALS_PATH')

        # check if we should mock or not
        self.in_production = ( enforce_production_p or mock_google_api == '0')
        self.google_drive_folder = google_drive_folder if google_drive_folder else os.getenv('GOOGLE_DRIVE_FOLDER')
        if self.in_production:
            assert self.google_drive_folder and credentials_filepath, "Missing environment variables"
        
        # generate credentials
        if self.in_production:
            secret_file = os.path.join(os.getcwd(), credentials_filepath)
            credentials = service_account.Credentials.from_service_account_file(secret_file, scopes=scopes)
            self.service = discovery.build("sheets", "v4", credentials=credentials)
            self.drive_service = discovery.build('drive', 'v3', credentials=credentials)

            # delete everything for the account
            if master_reset:
                query = "'me' in owners and trashed=false"
                files = self.drive_service.files().list(q=query).execute()["files"]
                client_email = credentials.service_account_email
                print(f"{client_email} has {len(files)} files/folders in their drive.")
                
                if len(files) == 0:
                    print("Master Reset not required.")
                else:
                    print("Master Reset will delete ALL FILES AND FOLDERS owned by the user.")
                    user_input = input(f"You want to proceed? (y/N) ")
                    if user_input.lower() in ['y', 'yes']:
                        for one_file in files:
                            print("deleteing file: ", one_file['name'])
                            self.drive_service.files().delete(fileId=one_file['id']).execute()
                        print("Master Reset complete.")
                    else:
                        print("Master Reset cancelled.")
                        exit()

            # create google folder using filename if not exists
            query = f"name='{self.google_drive_folder}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            files = self.drive_service.files().list(q=query).execute()["files"]

            if len(files) == 0:
                folder = self.drive_service.files().create(body={"name": self.google_drive_folder, "mimeType": "application/vnd.google-apps.folder"}).execute()
                assert folder, "Unable to create google drive folder"
                self.google_drive_folder = folder
                self.share_file(self.google_drive_folder['name'], "/", developer_gmail_list)
            else:
                self.google_drive_folder = files[0]
        else:
            self.google_drive_folder = {'id': 'mocked_root_folder_id', 'name': 'mocked_google_drive_folder_name'}

    # ------------------ GOOGLE SHEET ------------------

    def create_new_spreadsheet(self, filename, path, is_public_p=False, write_access_email=None):
        path = "/" + self.google_drive_folder['name'] + path
        check_validity(folder=path)
        
        if self.in_production:
            # create spreadsheet
            properties = { "properties": {"title": filename} }
            spreadsheet = self.service.spreadsheets().create(body=properties, fields='spreadsheetId').execute()
            spreadsheet_id = spreadsheet.get('spreadsheetId')
            assert spreadsheet_id, "Unable to create new spreadsheet"

            # apply permissions
            if is_public_p:
                permissions = {'type': 'anyone', 'role': 'writer'}
            else:
                assert write_access_email, "need email address to give write access on spreadsheet"
                permissions = {'type': 'user', 'role': 'writer', 'emailAddress': write_access_email}
            
            shareRes = self.drive_service.permissions().create(fileId=spreadsheet_id, body=permissions, fields='id').execute()

            # move spreadsheet to the correct path
            parent_folder_id = self.__create_path_if_not_exists(path)
            self.drive_service.files().update(fileId=spreadsheet['spreadsheetId'], addParents=parent_folder_id, removeParents='root').execute()
        else:
            spreadsheet_id = 'mocked_spreadsheet_id'
        
        return spreadsheet_id

    def get_spreadsheet_url(self, spreadsheet_id):
        if self.in_production:
            return 'https://docs.google.com/spreadsheets/d/' + spreadsheet_id

        return 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

    def append_spreadsheet(self, spreadsheet_id, sheet_name, rows):
        if self.in_production:
            body = {
                'values': rows
            }
            self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=sheet_name,
                body=body,
                valueInputOption='RAW'
            ).execute()
        
        return True

    def update_spreadsheet(self, spreadsheet_id, sheet_name, range_name, values):
        if self.in_production:
            sheetId = None
            if sheet_name:
                # get sheetId from sheet_name
                sheets = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()['sheets']
                for one_sheet in sheets:
                    if one_sheet['properties']['title'] == sheet_name:
                        sheetId = one_sheet['properties']['sheetId']
                        break
            
            # update spreadsheet
            body = {
                'valueInputOption': 'RAW',
                'data': [{
                    'range': range_name,
                    'majorDimension': 'ROWS',
                    'values': values
                }]
            }
            if sheetId:
                body['data'][0]['sheetId'] = sheetId
            self.service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        
        return True

    def delete_spreadsheet(self, spreadsheet_id):
        if self.in_production:
            self.drive_service.files().delete(fileId=spreadsheet_id).execute()
        return True

    # ------------------ SHEET INSIDE GOOGLE SHEET ------------------

    def create_new_sheet(self, spreadsheet_id, sheet_name):
        if self.in_production:
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
            }
            self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        
        return True

    def rename_sheet(self, spreadsheet_id, sheet_name, new_sheet_name):
        if self.in_production:
            # get sheetId from sheet_name
            sheets = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()['sheets']
            for one_sheet in sheets:
                if one_sheet['properties']['title'] == sheet_name:
                    sheetId = one_sheet['properties']['sheetId']
                    break
            
            # rename sheet
            body = {
                'requests': [{
                    'updateSheetProperties': {
                        'properties': {
                            'sheetId': sheetId,
                            'title': new_sheet_name
                        },
                        'fields': 'title'
                    }
                }]
            }
            self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        
        return True

    def delete_sheet(self, spreadsheet_id, sheet_name):
        if self.in_production:
            # get sheetId from sheet_name
            sheets = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()['sheets']
            for one_sheet in sheets:
                if one_sheet['properties']['title'] == sheet_name:
                    sheetId = one_sheet['properties']['sheetId']
                    break
            
            # delete sheet
            body = {
                'requests': [{
                    'deleteSheet': {
                        'sheetId': sheetId
                    }
                }]
            }
            self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        
        return True

    # ------------------ GOOGLE DRIVE ------------------

    def share_file(self, filename, path, gmail_list, role='writer'):
        path = "/" + self.google_drive_folder['name'] + path
        check_validity(folder=path)

        if self.in_production:
            file = self.get_file_by_name(filename, path=path)
            for one_gmail in gmail_list:
                permissions = {'type': 'user', 'role': role, 'emailAddress': one_gmail}
                shareRes = self.drive_service.permissions().create(fileId=file['id'], body=permissions, fields='id').execute()
                assert shareRes, f"Unable to share file with user: {one_gmail}"
        
        return True

    def get_files_by_path(self, path, mimeTypes=[]):
        path = "/" + self.google_drive_folder['name'] + path
        check_validity(folder=path)
        files = []
        
        if self.in_production:
            page_token = None
            parent_folder_id = self.__traverse_path(path)

            # generate search query
            search_query = f"trashed=false"
            if parent_folder_id:
                search_query += f" and '{parent_folder_id}' in parents"
            if mimeTypes:
                search_query += " and ("
                for one_mimeType in mimeTypes:
                    search_query += f"mimeType='{one_mimeType}' or "
                search_query = search_query[:-4] + ")"

            while True:
                response = self.drive_service.files().list(
                        q=search_query,
                        spaces="drive",
                        fields="nextPageToken, files(id, name)",
                        pageToken=page_token,
                    ).execute()
                files.extend(response.get("files", []))
                page_token = response.get("nextPageToken", None)
                if page_token is None:
                    break
        else:
            files = [
                {'id': 'mocked_file_id', 'name': 'mocked_file_name'},
                {'id': 'mocked_file_id_2', 'name': 'mocked_file_name_2'}
            ]

        return files

    def get_file_by_path(self, file_path):
        file_path = "/" + self.google_drive_folder['name'] + file_path
        check_validity(file=file_path)

        filename = file_path.split("/")[-1]
        path = file_path.replace(f"/{filename}", '/')

        if self.in_production:
            parent_folder_id = self.__traverse_path(path)
            
            # generate search query
            search_query = f"name='{filename}' and trashed=false"
            if parent_folder_id:
                search_query += f" and '{parent_folder_id}' in parents"
            
            results = self.drive_service.files().list(q=search_query).execute()
            items = results.get('files', [])
            if items:
                return items[0]
            return items

        return {'id': 'mocked_file_id', 'name': filename}

    def get_file_by_id(self, file_id):
        if self.in_production:
            return self.drive_service.files().get(fileId=file_id).execute()
        
        return {'id': file_id, 'name': 'mocked_file_name'}

    def get_file_by_name(self, filename, path="/"):
        path = "/" + self.google_drive_folder['name'] + path
        check_validity(folder=path)
        
        if self.in_production:
            parent_folder_id = self.__traverse_path(path)
            
            # generate search query
            search_query = f"name='{filename}' and trashed=false"
            if parent_folder_id:
                search_query += f" and '{parent_folder_id}' in parents"
            
            results = self.drive_service.files().list(q=search_query).execute()
            items = results.get('files', [])
            if items:
                return items[0]
            return None
        
        return {'id': 'mocked_file_id', 'name': filename}

    def get_file_size(self, file_path):
        file_path = "/" + self.google_drive_folder['name'] + file_path
        check_validity(file=file_path)

        filename = file_path.split("/")[-1]
        path = file_path.replace(f"/{filename}", '/')
        
        if self.in_production:
            parent_folder = self.__traverse_path(path)
            
            # generate search query
            search_query = f"name='{filename}' and trashed=false"
            if parent_folder:
                search_query += f" and '{parent_folder}' in parents"
            results = self.drive_service.files().list(q=search_query, fields="files(size)").execute()
            items = results.get('files', [])
            return items[0]['size']

        return '1024'

    def delete_file_by_id(self, file_id):
        if self.in_production:
            self.drive_service.files().delete(fileId=file_id).execute()
        
        return True

    def delete_file_by_path(self, file_path):
        file_path = "/" + self.google_drive_folder['name'] + file_path
        check_validity(file=file_path)

        filename = file_path.split("/")[-1]
        path = file_path.replace(f"/{filename}", '/')
        
        if self.in_production:
            parent_folder = self.__traverse_path(path)
            
            # generate search query
            search_query = f"name='{filename}' and trashed=false"
            if parent_folder:
                search_query += f" and '{parent_folder}' in parents"
            results = self.drive_service.files().list(q=search_query, fields="files(id)").execute()
            items = results.get('files', [])
            if items:
                file_id = items[0]['id']
                return self.delete_file_by_id(file_id)
            return False
        
        return True

    # ------------------ PRIVATE ------------------

    def __get_folder_id(self, folder_name, parent_id=None):
        if self.in_production:

            # Generate search query
            search_query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
            if parent_id:
                search_query += f" and '{parent_id}' in parents"

            results = self.drive_service.files().list(q=search_query, fields="files(id, name)").execute()
            items = results.get('files', [])
            if not items:
                return None
            else:
                return items[0]['id']  # Return the ID of the first found folder
        
        return 'mocked_folder_id'

    def __traverse_path(self, path):
        """Traverse a path in Google Drive and return the ID of the last folder."""
        check_validity(folder=path)
        folders = path.strip('/').split('/')

        if self.in_production:
            current_id = None
            for folder_name in folders:
                current_id = self.__get_folder_id(folder_name, current_id)
                if current_id is None:
                    break
        else:
            current_id = 'mocked_folder_id'
        
        return current_id

    def __create_path_if_not_exists(self, path):
        """Create the path if it does not exist and return the ID of the last folder."""
        check_validity(folder=path)
        folders = path.strip('/').split('/')

        if self.in_production:
            current_id = None
            for folder_name in folders:
                next_id = self.__get_folder_id(folder_name, current_id)
                if next_id is None:
                    # Folder doesn't exist, so create it
                    next_id = self.__create_folder(folder_name, current_id)
                current_id = next_id
        else:
            current_id = 'mocked_folder_id'

        return current_id

    def __create_folder(self, folder_name, parent_id=None):
        """Create a new folder in Google Drive."""
        if self.in_production:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]

            folder = self.drive_service.files().create(body=file_metadata, fields='id').execute()
            return folder.get('id')

        return 'newly_created_folder_id'

# ------------------ HELPERS ------------------

def check_validity(file=None, folder=None):
    if file:
        assert file.startswith("/"), "file must start with '/'"
        assert file != "/" and not file.endswith("/"), "file must not end with '/'"
    if folder:
        assert folder.startswith("/"), "folder must start with '/'"
        assert folder.endswith("/"), "folder must end with '/'"