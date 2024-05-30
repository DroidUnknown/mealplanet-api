import pytest

from utils import google_utils

google_drive_folder = "test-folder"
spreadsheet = {
    "id": None,
    "name": 'spreadsheet-1',
    "path": "/test-1/",
    "url": None,
    "sheets": []
}

@pytest.fixture(scope="module", autouse=True)
def google_helper():
    google_helper = google_utils.GoogleUtils(google_drive_folder=google_drive_folder)
    yield google_helper

def test_create_new_spreadsheet(google_helper):
    global spreadsheet

    spreadsheet_id = google_helper.create_new_spreadsheet(spreadsheet["name"], spreadsheet["path"], is_public_p=True)
    assert spreadsheet_id is not None
    # print(f"Spreadsheet created with ID: {spreadsheet_id}")

    spreadsheet["id"] = spreadsheet_id
    spreadsheet["sheets"] = ["Sheet1"]

def test_get_spreadsheet_url(google_helper):
    global spreadsheet
    spreadsheet_url = google_helper.get_spreadsheet_url(spreadsheet["id"])

    assert spreadsheet_url is not None, "Public URL is None"
    # print(f"Public URL: {spreadsheet_url}")

    spreadsheet["url"] = spreadsheet_url

def test_append_spreadsheet(google_helper):
    global spreadsheet

    sheet_name = "Sheet1"
    rows = [
        ["A1", "B1", "C1"],
    ]
    successful = google_helper.append_spreadsheet(spreadsheet["id"], sheet_name, rows)
    assert successful, "Append spreadsheet failed"
    # print(f"data appended to spreadsheet at: {spreadsheet['url']}")

def test_update_spreadsheet(google_helper):
    global spreadsheet

    sheet_name = "Sheet1"
    range_name = "A1:C1"
    values = [
        ["X1", "Y1", "Z1"],
    ]
    successful = google_helper.update_spreadsheet(spreadsheet['id'], sheet_name, range_name, values)
    assert successful, "Update spreadsheet failed"
    # print(f"data updated in spreadsheet at: {spreadsheet['url']}")

def test_create_new_sheet(google_helper):
    global spreadsheet
    new_sheet_name = "Sheet2"

    successful = google_helper.create_new_sheet(spreadsheet["id"], new_sheet_name)
    assert successful, "Create new sheet failed"
    # print(f"new sheet created in spreadsheet at: {spreadsheet['url']}")

    spreadsheet["sheets"].append(new_sheet_name)

def test_rename_sheet(google_helper):
    global spreadsheet
    old_sheet_name = spreadsheet["sheets"][0]
    new_sheet_name = old_sheet_name + "-renamed"

    successful = google_helper.rename_sheet(spreadsheet["id"], old_sheet_name, new_sheet_name)
    assert successful, "Rename sheet failed"
    # print(f"sheet renamed in spreadsheet at: {spreadsheet['url']}")

    spreadsheet["sheets"][0] = new_sheet_name

def test_delete_sheet(google_helper):
    global spreadsheet
    sheet_name = "sheet-to-be-deleted"

    successful = google_helper.create_new_sheet(spreadsheet["id"], sheet_name)
    assert successful, "Create new sheet failed"

    successful = google_helper.delete_sheet(spreadsheet["id"], sheet_name)
    assert successful, "Delete sheet failed"

    # print(f"sheet named {sheet_name} deleted in spreadsheet at: {spreadsheet['url']}")

def test_delete_spreadsheet(google_helper):
    spreadsheet_name = 'spreadsheet-2'
    path = "/test-1/"

    spreadsheet_id = google_helper.create_new_spreadsheet(spreadsheet_name, path, is_public_p=True)
    assert spreadsheet_id, f"Unable to create new spreadsheet named: {spreadsheet_name}"

    successful = google_helper.delete_spreadsheet(spreadsheet_id)
    assert successful, "Delete spreadsheet failed"

def test_get_files_by_path(google_helper):
    global spreadsheet

    # try once without mimeTypes
    files = google_helper.get_files_by_path(spreadsheet["path"])
    assert len(files) > 0, "No files found"

    mimeTypes=["application/vnd.google-apps.spreadsheet"]

    # try again with mimeTypes
    files = google_helper.get_files_by_path(spreadsheet["path"], mimeTypes)
    assert len(files) > 0, "No files found"

def test_get_file_by_path(google_helper):
    global spreadsheet

    file_path = spreadsheet["path"] + spreadsheet["name"]
    successful = google_helper.get_file_by_path(file_path)
    assert successful, "Get file by path failed"

def test_get_file_by_id(google_helper):
    global spreadsheet

    successful = google_helper.get_file_by_id(spreadsheet["id"])
    assert successful, "Get file by id failed"

def test_get_file_by_name(google_helper):
    global spreadsheet

    successful = google_helper.get_file_by_name(spreadsheet["name"], spreadsheet["path"])
    assert successful, "Get file by name failed"

def test_get_file_size(google_helper):
    global spreadsheet
    file_path = spreadsheet["path"] + spreadsheet["name"]

    successful = google_helper.get_file_size(file_path)
    assert successful, "Get file size failed"

@pytest.fixture(scope="module", autouse=True)
def teardown_module(google_helper):
    # setup code ( if any ) goes here
    yield

    global spreadsheet, google_drive_folder
    # print("\n\ntearing down test_google_utils.py")

    # delete spreadsheet
    successful = google_helper.delete_file_by_id(spreadsheet["id"])
    assert successful, "Delete file by id failed"

    # delete folder which contains spreadsheet
    path = spreadsheet["path"]
    folder_path = path[:-1]
    successful = google_helper.delete_file_by_path(folder_path)
    assert successful, "Delete file by path failed"