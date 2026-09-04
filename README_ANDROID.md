# AU Result Analyser — Android Wrapper

## What's inside
- `android/` — full Android WebView app project (loads your Streamlit app), with a custom "AU" launcher icon already generated in all densities.
- `.github/workflows/build-apk.yml` — GitHub Action that builds the APK automatically.

## How to use
1. Extract this zip.
2. Copy the `android/` folder and `.github/` folder into the ROOT of your GitHub repo
   (`AU_Result_Analyser/`), next to your existing `AU_Result_Analyzer/app.py` folder.
   So it looks like:
   ```
   AU_Result_Analyser/
   ├── AU_Result_Analyzer/app.py   (your existing Streamlit code)
   ├── android/                    (new)
   └── .github/workflows/build-apk.yml   (new)
   ```
3. Commit and push to the `main` branch.
4. Go to your repo's **Actions** tab → "Build APK" → **Run workflow** (or it auto-runs on push).
5. When the run finishes (green check), open it → under **Artifacts**, download
   **AU-Result-Analyser-APK** → unzip → you get `app-release.apk`.
6. Transfer to your phone and install (allow "install unknown apps" if prompted).

## Notes
- The APK is unsigned/debug-style — fine for personal installs, not for Play Store.
- App name shown on the phone: "AU Result Analyser", with the custom icon.
- To change the icon later, just replace the PNGs in `android/app/src/main/res/mipmap-*/`.
- To change the loaded URL, edit `URL` in `MainActivity.java`.
