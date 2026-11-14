# graph-interpreter
Project for NE 111 @uwaterloo

## Photo viewer

### First-time setup

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if it
   is not already installed. For example, in PowerShell:

   ```powershell
   winget install --id=astral-sh.uv -e
   ```

   Close and reopen the terminal after installation.
2. Open PowerShell or a terminal in this project folder (the folder containing
   `app.py`).
3. Create a virtual environment with uv:

   ```powershell
   uv venv
   ```

4. Install the app's requirements with uv:

   ```powershell
   uv pip install --python .venv\Scripts\python.exe -r requirements.txt
   ```

### Start the app

1. In PowerShell or a terminal, go to the project folder.
2. Run:

   ```powershell
   uv run --python .venv\Scripts\python.exe -m streamlit run app.py
   ```

3. Open the **Local URL** printed in the terminal (usually
   `http://localhost:8501`) in your browser.
4. Click **Browse files**, choose an image (such as JPG, JPEG, PNG, WebP, BMP,
   GIF, or TIFF), and the photo will appear on the page.
5. To stop the app, return to the terminal and press **Ctrl+C**.

After the first-time setup, repeat only the steps under **Start the app** each
time you want to run the photo viewer.
