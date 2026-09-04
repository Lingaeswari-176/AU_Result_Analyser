# AU Result Analyzer Android APK

This is a lightweight Android wrapper for the deployed Streamlit application.

App URL:
https://auresultanalyser-b5acl3evfarngeikzan3nu.streamlit.app/

Features:
- Opens the existing Streamlit analyzer as an Android app
- PDF file picker support
- Download/open support for generated reports
- Portrait layout
- Custom AU Result Analyzer icon
- No Android Studio required

## Build without Android Studio

1. Put this project into your GitHub repository.
2. Push to `main` or `master`.
3. Open GitHub -> Actions -> `Build AU Result Analyzer APK`.
4. Wait for the workflow to finish.
5. Open the workflow run and download the `AU-Result-Analyzer-APK` artifact.
6. Extract it and install `app-debug.apk` on Android.

Important:
This APK is a wrapper around the Streamlit website. The APK itself does not contain the Python parser. Internet access is required, and the Streamlit deployment must remain available.
