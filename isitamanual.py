def upload_to_drive(zip_file_path, credentials):
    try:
        # Build the service with the provided credentials
        service = build('drive', 'v3', credentials=credentials)

        # Prepare file metadata and media upload
        file_metadata = {
            'name': os.path.basename(zip_file_path),
            'mimeType': 'application/zip'
        }
        media = MediaFileUpload(zip_file_path, mimetype='application/zip', resumable=True)
        
        # Create the file on Google Drive
        file = service.files().create(body=file_metadata, media_body=media, fields='id,webViewLink').execute()

        # Make the file publicly accessible
        service.permissions().create(
            fileId=file['id'],
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        # Clear credentials after successful upload
        del credentials  # Remove credentials after use (clearing the session credentials)
        
        # Return the link to the uploaded file
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"An error occurred while uploading to Google Drive: {e}")
        st.error(traceback.format_exc())
        return None
