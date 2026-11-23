# graph-interpreter
Project for NE 111 @uwaterloo

## Graph digitizer

The app extracts data points from a graph image in two steps:

1. Upload an image and name the data set and axes. The data set name appears
   above the image, the y-axis name to its left, and the x-axis name beneath
   it. Four labeled calibration markers appear near the image
   corners: the first x/y references start at the lower-left, the second x
   reference at the lower-right, and the second y reference at the upper-left.
   Drag them onto the graph's known axis points. A marker's tip shows its exact
   location as you drag; x-axis tips face up, and y-axis tips face right. Enter
   the corresponding known values (they do not need to start at zero) and
   choose linear or logarithmic scale independently for each axis. Values
   remain editable during extraction, and changing one recalibrates all
   extracted points. Alternatively, choose a reference under **Reference
   point to reposition** and click its corrected location. Choose **Do not
   reposition a reference** to resume adding data points.
2. Click the graph's data points to convert them to x/y values. The extracted
   points appear in a table and can be downloaded as a CSV file. Select a point
   below the table and choose **Remove selected point** to remove it. The CSV's
   first row contains the data set name, and its second row contains column
   headers using the names given to the axes.
3. After calibration, choose **Detect colored data sets** to identify colored
   lines or scatter series in the calibrated plot area. Review the marked
   trace pixels, rename or exclude detected series, and export the selected
   series together. Legend text is recognized locally when Tesseract is
   installed; otherwise, enter the series names yourself. Detection separates
   visibly distinct colors; grayscale traces and same-colored overlapping
   series still need the existing click-to-add workflow. Download each
   selected series as its own CSV (series name, two axis headers, and two
   columns of points), or export selected series together. For best results,
   place X1 and X2 at the lower-left and lower-right plot edges and Y1 and Y2
   at the lower-left and upper-left plot edges.

### Run the app on Windows

Install Python 3.10 or newer if it is not already installed. In PowerShell, you
can install Python 3.12 with:

```powershell
winget install --id Python.Python.3.12 -e
```

Install the local OCR engine to recognize legend labels:

```powershell
winget install --id UB-Mannheim.TesseractOCR -e
```

Close and reopen PowerShell after installation so the Tesseract executable is
available on `PATH`. Legend recognition is optional; series detection and
manual series naming work without it.

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
