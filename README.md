# graph-interpreter
Project for NE 111 @uwaterloo

## Graph digitizer

The app extracts data points from a graph image in two steps:

1. Upload an image. Four labeled calibration markers appear near the image
   corners: the first x/y references start at the lower-left, the second x
   reference at the lower-right, and the second y reference at the upper-left.
   Drag them onto the graph's known axis points. A marker's tip shows its exact
   location as you drag; x-axis tips face up, and y-axis tips face right. Enter
   the corresponding known values (they do not need to start at zero). Values
   remain editable during extraction, and changing one recalibrates all
   extracted points. Alternatively, choose a reference under **Reference
   point to reposition** and click its corrected location. Choose **Do not
   reposition a reference** to resume adding data points.
2. Click the graph's data points to convert them to x/y values. The extracted
   points appear in a table and can be downloaded as a CSV file. Select a point
   below the table and choose **Remove selected point** to remove it.

### Run the app on Windows

Install Python 3.10 or newer if it is not already installed. In PowerShell, you
can install Python 3.12 with:

```powershell
winget install --id Python.Python.3.12 -e
```

If you install Python this way, close and reopen PowerShell afterward. Then
open PowerShell in this project folder (the folder containing `app.py`) and
paste this whole block. It creates the virtual environment if needed, installs
the requirements, starts Streamlit, and opens the app in your browser:

```powershell
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3 -m venv .venv
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        python -m venv .venv
    } else {
        throw "Python was not found. Install Python 3.10 or newer, reopen PowerShell, and try again."
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the virtual environment."
    }
}

$python = ".\.venv\Scripts\python.exe"
& $python -m pip --version 2>$null
if ($LASTEXITCODE -ne 0) {
    & $python -m ensurepip --upgrade
    if ($LASTEXITCODE -ne 0) {
        throw "Could not enable pip in the virtual environment."
    }
}

& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    throw "Could not install the app requirements."
}

& $python -m streamlit run app.py --server.headless false
```

Choose an image (JPG, JPEG, PNG, WebP, BMP, GIF, or TIFF) and follow the
on-screen prompts. To stop the app, return to PowerShell and press **Ctrl+C**.

### Start it next time

After the setup block has succeeded once, open PowerShell in the project folder
and run only:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.headless false
```
