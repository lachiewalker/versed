import io
from pathlib import Path
from typing import Dict
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


class GoogleDriveHandler:
    def __init__(self, credentials):
        self.credentials = credentials

    def _get_google_drive_file_stream(self, file: Dict) -> Dict:
        """
        Gets the file stream of a file from Google Drive.

        Args:
            file (dict): {"name": file_name, "path": Google Drive file ID}

        Returns:
            Dict: {
                "stream": io.BytesIO: The file stream of the file,
                "type": str: The file extension of the file
            }
        """
        extension = Path(file["name"]).suffix
        file_id = file["path"].split("/")[-1]
        match extension:
            case ".txt" | ".pdf" | ".ipynb" | ".docx" | ".xlsx" | ".pptx" | ".csv":
                file["stream"] = self._get_raw_file_stream(file_id)
                file["type"] = extension
            case ".gdoc":
                file["stream"] = self._get_google_doc_file_stream(file_id)
                file["type"] = ".docx"
            case ".gsheet":
                file["stream"] = self._get_google_sheet_file_stream(file_id)
                file["type"] = ".gsheet"
            case ".gslides":
                file["stream"] = self._get_google_slide_file_stream(file_id)
                file["type"] = ".gslides"
            case _:
                raise ValueError(f"Unsupported file type: {extension}")
        
        return file

    # Methods to get file streams:

    def _get_raw_file_stream(self, file_id: str) -> io.BytesIO:
        """
        Gets the file stream of a .txt file from Google Drive.
        """
        service = build('drive', 'v3', credentials=self.credentials)
        return self._download_file_stream(service, file_id)

    def _get_google_doc_file_stream(self, file_id: str) -> io.BytesIO:
        """
        Gets the file stream of a Google Doc as a .docx file.
        """
        service = build('drive', 'v3', credentials=self.credentials)
        return self._export_file_stream(
            service, file_id, mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    def _get_google_sheet_file_stream(self, file_id: str) -> io.BytesIO:
        """
        Gets the file stream of a Google Sheet as a .csv file.
        """
        service = build('drive', 'v3', credentials=self.credentials)
        return self._export_file_stream(service, file_id, mime_type="text/csv")
    
    def _get_google_slide_file_stream(self, file_id: str) -> io.BytesIO:
        """
        Gets the file stream of a Google Slide as a .pptx file.

        Args:
            file_id (str): The ID of the Google Slides file.

        Returns:
            io.BytesIO: The file stream of the exported .pptx file.
        """
        service = build('drive', 'v3', credentials=self.credentials)
        return self._export_file_stream(
            service, file_id, mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )

    # Utility methods:

    def _download_file_stream(self, service, file_id: str) -> io.BytesIO:
        """
        Downloads a file stream from Google Drive.

        Args:
            service: Google Drive API service instance.
            file_id (str): The file ID.

        Returns:
            io.BytesIO: The file stream.
        """
        request = service.files().get_media(fileId=file_id)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
        file_stream.seek(0)
        return file_stream

    def _export_file_stream(self, service, file_id: str, mime_type: str) -> io.BytesIO:
        """
        Exports a Google Drive file to a specific MIME type and gets the file stream.

        Args:
            service: Google Drive API service instance.
            file_id (str): The file ID.
            mime_type (str): The MIME type to export.

        Returns:
            io.BytesIO: The exported file stream.
        """
        request = service.files().export_media(fileId=file_id, mimeType=mime_type)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
        file_stream.seek(0)
        return file_stream
