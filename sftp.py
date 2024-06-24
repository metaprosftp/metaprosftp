def main():
    """Main function for the Streamlit app."""
    
    # Apply custom styling
    st.markdown("""
    <style>
        #MainMenu, header, footer {visibility: hidden;}
        section[data-testid="stSidebar"] div:first-child {top: 0; height: 100vh;}
    </style>
    """, unsafe_allow_html=True)

    # Check if user is logged in
    if not st.session_state['logged_in']:
        # Display login form
        # Use custom HTML and CSS to style the title
        st.markdown("""
    <style>
    .small-title {
        font-size: 1.5em; /* Adjust the size as needed */
    }
    </style>
    <h1 class="small-title">Login</h1>
    """, unsafe_allow_html=True)

        username = st.text_input("Username")
        password = st.text_input("Password", type='password')

        if st.button("Login"):
            # Validate login credentials
            correct_username = "dian"
            correct_password = "trial"

            if username == correct_username and password == correct_password:
                if check_lock():
                    st.error("Another user is currently logged in. Please try again later.")
                else:
                    st.session_state['logged_in'] = True
                    set_lock("logged_in")
                    st.success("Login successful! Please click the login button once more.")
            else:
                st.error("Invalid username or password.")
        return

    # Display "About" button at the top
    if st.button("About"):
        st.markdown("""
        ### Why Choose MetaPro?

        **AI-Powered Precision:** Leverage the power of Google Generative AI to automatically generate highly relevant and descriptive titles and tags for your images. Enhance your image metadata with unprecedented accuracy and relevance.

        **Streamlined Workflow:** Upload your images in just a few clicks. Our app processes each photo, embeds the generated metadata, and prepares it for upload—automatically and effortlessly.

        **Secure and Efficient Gdrive Upload:** Once processed, your images are securely uploaded to gdrive. Keep your workflow smooth and your data safe with our robust upload system.

        *How It Works:*
        1. Upload Your Images: Drag and drop your JPG/JPEG files into the uploader.
        2. Generate Metadata: Watch as the app uses AI to create descriptive titles and relevant tags.
        3. Embed Metadata: The app embeds the metadata directly into your images.
        4. Directly upload to Google Drive for faster downloads.
        
        **Subscribe Now and Experience the Difference:**
        - **MetaPro Basic Plan: $10 for 3 months – Upload up to 1,000 images daily.
        - **MetaPro Premium Plan: $40 for unlimited image uploads for a lifetime.

        Ready to revolutionize your workflow? Subscribe today and take the first step towards a smarter, more efficient image management solution.

        """)

    # Check logout at the end
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        set_lock("")
        st.success("Logged out successfully.")
        return

    # Check lock file before proceeding
    if not check_lock():
        st.error("Access denied. Your MetaPro Basic Plan subscription is limited to only one device.")
        return

    # Display WhatsApp chat link
    st.markdown("""
    <div style="text-align: center; margin-top: 20px;">
        <a href="https://wa.me/6285328007533" target="_blank">
            <button style="background-color: #1976d2; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                MetaPro
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

    # Check if license has already been validated
    license_file = "license.txt"
    if not st.session_state['license_validated']:
        if os.path.exists(license_file):
            with open(license_file, 'r') as file:
                start_date_str = file.read().strip()
                start_date = datetime.fromisoformat(start_date_str)
                st.session_state['license_validated'] = True
        else:
            # License key input
            validation_key = st.text_input('License Key', type='password')

    # Check if validation key is correct
    correct_key = "31days"

    if not st.session_state['license_validated'] and validation_key:
        if validation_key == correct_key:
            st.session_state['license_validated'] = True
            start_date = datetime.now(JAKARTA_TZ)
            with open(license_file, 'w') as file:
                file.write(start_date.isoformat())
        else:
            st.error("Invalid validation key. Please enter the correct key.")

    if st.session_state['license_validated']:
        # Check the license file for the start date
        with open(license_file, 'r') as file:
            start_date_str = file.read().strip()
            start_date = datetime.fromisoformat(start_date_str)

        # Calculate the expiration date
        expiration_date = start_date + timedelta(days=31)
        current_date = datetime.now(JAKARTA_TZ)

        if current_date > expiration_date:
            st.error("Your license has expired. Please contact support for a new license key.")
            return
        else:
            days_remaining = (expiration_date - current_date).days
            st.success(f"License valid. You have {days_remaining} days remaining.")

        # API Key input
        api_key = st.text_input('Enter your API Key', value=st.session_state['api_key'] or '')
        
        # Save API key in session state
        if api_key:
            st.session_state['api_key'] = api_key
            
        # SFTP Password input
        sftp_password = st.text_input('SFTP Password', type='password')   

        # Upload image files
        uploaded_files = st.file_uploader('Upload Images (Only JPG and JPEG supported)', accept_multiple_files=True)

        if uploaded_files:
            valid_files = [file for file in uploaded_files if file.type in ['image/jpeg', 'image/jpg']]
            invalid_files = [file for file in uploaded_files if file not in valid_files]

            if invalid_files:
                st.error("Only JPG and JPEG files are supported.")

            if valid_files and st.button("Process"):
                with st.spinner("Processing..."):
                    try:
                        # Check and update upload count for the current date
                        if st.session_state['upload_count']['date'] != current_date.date():
                            st.session_state['upload_count'] = {
                                'date': current_date.date(),
                                'count': 0
                            }
                        
                        # Check if remaining uploads are available
                        if st.session_state['upload_count']['count'] + len(valid_files) > 1000:
                            remaining_uploads = 1000 - st.session_state['upload_count']['count']
                            st.warning(f"You have exceeded the upload limit. Remaining uploads for today: {remaining_uploads}")
                            return
                        else:
                            st.session_state['upload_count']['count'] += len(valid_files)
                            st.success(f"Uploads successful. Remaining uploads for today: {1000 - st.session_state['upload_count']['count']}")

                        genai.configure(api_key=api_key)  # Configure AI model with API key
                        model = genai.GenerativeModel('gemini-pro-vision')

                        # Create a temporary directory to store the uploaded images
                        with tempfile.TemporaryDirectory() as temp_dir:
                            # Save the uploaded images to the temporary directory
                            image_paths = []
                            for file in valid_files:
                                temp_image_path = os.path.join(temp_dir, file.name)
                                with open(temp_image_path, 'wb') as f:
                                    f.write(file.read())
                                image_paths.append(temp_image_path)

                            total_files = len(image_paths)
                            files_processed = 0

                            progress_placeholder = st.empty()  # Initialize a single progress bar placeholder
                            status_text = st.empty()  # Initialize status text placeholder

                            # Process each image one by one
                            for image_path in image_paths:
                                try:
                                    # Update progress text
                                    progress_placeholder.progress(files_processed / total_files)
                                    status_text.text(f"Processing {files_processed}/{total_files} images. Uploaded to SFTP: {files_processed}")

                                    # Open image
                                    img = Image.open(image_path)

                                    # Generate metadata
                                    metadata = generate_metadata(model, img)

                                    # Embed metadata
                                    updated_image_path = embed_metadata(image_path, metadata, progress_placeholder, files_processed, total_files)
                                    
                                    # Upload via SFTP
                                    if updated_image_path:
                                        sftp_upload(updated_image_path, sftp_password, progress_placeholder, files_processed, total_files)
                                        files_processed += 1

                                except Exception as e:
                                    st.error(f"An error occurred while processing {os.path.basename(image_path)}: {e}")
                                    st.error(traceback.format_exc())
                                    continue

                            progress_placeholder.progress(files_processed / total_files)
                            status_text.text(f"Processing {files_processed}/{total_files} images. Uploaded to SFTP: {files_processed}")
                            st.success(f"Successfully processed and transferred {files_processed} files to the SFTP server.")

                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                        st.error(traceback.format_exc())  # Print detailed error traceback for debugging

if __name__ == '__main__':
    main()
