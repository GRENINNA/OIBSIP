# Task 2 - BMI Calculator

A modular desktop application for calculating, classifying, saving, and
visualising Body Mass Index (BMI) records. The project uses Tkinter for the
graphical interface, SQLite for local history, and either Matplotlib or a
built-in Tkinter Canvas for trend charts.

## Table of contents

- [Features](#features)
- [Technology](#technology)
- [Project structure](#project-structure)
- [Installation](#installation)
- [Running the application](#running-the-application)
- [How to use the application](#how-to-use-the-application)
- [Button reference](#button-reference)
- [BMI calculation and categories](#bmi-calculation-and-categories)
- [Input validation](#input-validation)
- [History and multi-user support](#history-and-multi-user-support)
- [BMI trend chart](#bmi-trend-chart)
- [Database storage](#database-storage)
- [Clearing the database](#clearing-the-database)
- [Troubleshooting](#troubleshooting)
- [Privacy and medical notice](#privacy-and-medical-notice)

## Features

- Graphical interface built with Tkinter; no command-line input is required
- Calculates BMI using weight in kilograms and height in metres
- Displays BMI rounded to two decimal places
- Classifies results as Underweight, Normal, Overweight, or Obese
- Applies a different result colour to each category
- Rejects empty, non-numeric, zero, negative, infinite, and invalid values
- Supports records for multiple named users
- Stores historical measurements in a local SQLite database
- Reloads a selected user's history without restarting the application
- Displays recorded date, weight, height, BMI, and category in a table
- Plots BMI history with Matplotlib when available
- Automatically uses a built-in Tkinter chart when Matplotlib is unavailable
- Shows database, validation, and chart errors inside the GUI
- Keeps calculation, database, and interface responsibilities in separate modules

## Technology

| Component | Purpose |
| --- | --- |
| Python 3.10+ | Programming language |
| Tkinter and ttk | Desktop interface and styled widgets |
| SQLite through `sqlite3` | Local user and BMI history storage |
| Tkinter Canvas | Dependency-free BMI trend line chart |
| Matplotlib (optional) | Enhanced trend chart with navigation controls |
| `datetime` | Local record timestamps and chart dates |

Tkinter and SQLite are included with standard Python installations. The
built-in chart requires no third-party package. Matplotlib is an optional
enhancement listed separately in `requirements-matplotlib.txt`.

## Project structure

```text
Python-Task2-BMICalculator/
|-- main.py
|-- requirements.txt
|-- requirements-matplotlib.txt
|-- README.md
|-- bmi_history.db              # Created automatically at runtime
`-- bmi_app/
    |-- __init__.py
    |-- logic.py
    |-- database.py
    |-- chart.py
    `-- ui.py
```

### File responsibilities

| File | Responsibility |
| --- | --- |
| `main.py` | Creates the Tkinter root window and starts the event loop |
| `bmi_app/logic.py` | Validates measurements, calculates BMI, and assigns categories and colours |
| `bmi_app/database.py` | Creates the database and saves or retrieves BMI records |
| `bmi_app/chart.py` | Opens a Matplotlib chart or the automatic Tkinter fallback |
| `bmi_app/ui.py` | Builds the interface and coordinates calculations, history, and charts |
| `bmi_app/__init__.py` | Marks `bmi_app` as an importable Python package |
| `requirements.txt` | Confirms that the built-in chart has no third-party dependency |
| `requirements-matplotlib.txt` | Declares the optional Matplotlib enhancement |
| `bmi_history.db` | Runtime SQLite database; it is not part of the source code |

## Installation

### Option 1: Standard installation

Open PowerShell in the project folder:

```powershell
Set-Location "D:\OIBSIP\Python-Task2-BMICalculator"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The built-in chart works after this step without Matplotlib. To enable the
enhanced Matplotlib chart and navigation toolbar, optionally run:

```powershell
python -m pip install --prefer-binary -r requirements-matplotlib.txt
```

Using `python -m pip` ensures that an optional package is installed for the
same Python interpreter used to run the application.

### Option 2: Virtual environment

A virtual environment keeps project packages separate from other Python
projects:

```powershell
Set-Location "D:\OIBSIP\Python-Task2-BMICalculator"
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Running the application

Start the application from the project folder:

```powershell
python main.py
```

Execute only `main.py`. The files inside `bmi_app` are modules imported by the
entry point and are not intended to be started separately.

If multiple Python versions are installed, use the full path to the interpreter
you want to run:

```powershell
& "C:\Path\To\Python\python.exe" main.py
```

## How to use the application

1. Enter a name, such as `Alice`.
2. Enter weight in kilograms, such as `70`.
3. Enter height in metres, such as `1.75`.
4. Select **Calculate BMI** to calculate without saving.
5. Review the rounded BMI and colour-coded category.
6. Select **Save record** to store the measurement under the entered name.
7. Select or type a name and choose **Refresh** to reload that user's records.
8. Choose **View BMI trend** to open the user's chart.

### Important height format

Height must be entered in metres:

| Height | Correct entry |
| --- | --- |
| 170 centimetres | `1.70` |
| 175 centimetres | `1.75` |
| 182 centimetres | `1.82` |

Entering `170` means 170 metres. For example, `70 / 170^2` is approximately
`0.0024`, which rounds to `0.00` and is classified as Underweight. Enter `1.70`
instead.

## Button reference

| Button | Function |
| --- | --- |
| **Calculate BMI** | Reads the weight and height, validates them, and displays a result without saving it |
| **Save record** | Recalculates the current values and saves them under the entered name |
| **Refresh** | Clears the visible history table and reloads records for the selected or typed name |
| **View BMI trend** | Loads the selected user's records and opens Matplotlib or the built-in Tkinter chart |

The **Refresh** button does not calculate, save, edit, or delete records. It only
reloads saved history from `bmi_history.db`.

## BMI calculation and categories

The application uses this formula:

```text
BMI = weight in kilograms / (height in metres x height in metres)
```

Example for 70 kg and 1.75 m:

```text
BMI = 70 / (1.75 x 1.75)
BMI = 22.857...
Displayed BMI = 22.86
Category = Normal
```

### Categories

| BMI range | Category | Display colour |
| --- | --- | --- |
| Below 18.5 | Underweight | Blue |
| 18.5 to below 25.0 | Normal | Green |
| 25.0 to below 30.0 | Overweight | Orange |
| 30.0 and above | Obese | Red |

The application compares the full calculated value before rounding it for
display.

## Input validation

The application rejects:

- Missing weight or height
- Text such as `seventy`
- Zero weight or height
- Negative measurements
- Infinite or non-finite numbers
- Names longer than 100 characters
- A missing name when saving or viewing history

Calculation itself does not require a name. Saving records, loading history, and
opening a trend graph require one.

## History and multi-user support

Each record is associated with a user name. User-name matching is
case-insensitive, so `Alice` and `alice` refer to the same saved history.

When records are loaded, the table displays:

- Local date and time
- Weight in kilograms
- Height in metres
- BMI rounded to two decimal places
- BMI category

The newest saved measurements are displayed first. Selecting a saved name from
the name list automatically refreshes the history table. The **Refresh** button
is useful after typing a name manually or when another application instance has
changed the database.

## BMI trend chart

The trend chart requires at least one saved record for the selected user. It
uses Matplotlib when that package imports successfully. Otherwise, it
automatically opens a responsive Tkinter Canvas chart, so the feature remains
available without extra packages.

To create a useful trend:

1. Save several measurements under the same user name.
2. Select that user.
3. Choose **View BMI trend**.

The graph displays dates along the horizontal axis and BMI values along the
vertical axis. The green shaded area marks the application's Normal category,
and horizontal reference lines mark category boundaries.

Matplotlib is optional. To enable its enhanced chart toolbar, install it with:

```powershell
python -m pip install --prefer-binary -r requirements-matplotlib.txt
```

## Database storage

The database file is created automatically at:

```text
D:\OIBSIP\Python-Task2-BMICalculator\bmi_history.db
```

The `bmi_records` table stores:

| Column | Stored value |
| --- | --- |
| `id` | Automatically generated record identifier |
| `user_name` | Name entered in the GUI |
| `weight_kg` | Weight in kilograms |
| `height_m` | Height in metres |
| `bmi` | Full calculated BMI value |
| `category` | Underweight, Normal, Overweight, or Obese |
| `recorded_at` | Local timestamp including time-zone information |

No BMI information is transmitted over the internet. The data remains in this
local SQLite file.

## Clearing the database

Close every running BMI Calculator window before modifying the database.

### Keep a backup

Rename the existing database:

```powershell
Set-Location "D:\OIBSIP\Python-Task2-BMICalculator"
Rename-Item -LiteralPath ".\bmi_history.db" -NewName "bmi_history_backup.db"
```

The next application start creates a new empty `bmi_history.db`. The old records
remain recoverable in `bmi_history_backup.db`.

### Permanently remove all records

```powershell
Remove-Item -LiteralPath "D:\OIBSIP\Python-Task2-BMICalculator\bmi_history.db"
```

Restart `main.py`. The application recreates the database automatically. The
deleted records cannot be restored unless a backup exists.

## Troubleshooting

### BMI always displays `0.00` and Underweight

The height was probably entered in centimetres. Enter `1.70` instead of `170`.

### `ModuleNotFoundError: No module named 'matplotlib'`

The updated application automatically opens its built-in Tkinter graph, so this
error no longer prevents trend viewing. Matplotlib is optional. To install the
enhanced backend, use the same Python interpreter that starts the app:

```powershell
python -m pip install --prefer-binary -r requirements-matplotlib.txt
python -c "import matplotlib; print(matplotlib.__version__)"
python main.py
```

If installation tries to compile Matplotlib and fails on Windows, use a current
64-bit Python installation or continue using the built-in chart.

### The history table is empty

- Confirm that a record was saved rather than only calculated.
- Enter or select the same user name used when saving.
- Select **Refresh**.
- Check the status line for a database error.

### The trend graph has no data

Save at least one record for the selected user, then refresh the history and
open the graph again.

### Database is locked or unavailable

Close other copies of the application and confirm that the project directory is
writable. Do not open `bmi_history.db` in another database editor while saving a
record.

### Tkinter window does not open

Run this check:

```powershell
python -m tkinter
```

If no test window opens, repair or reinstall Python with the Tcl/Tk component
enabled.

## GitHub notes

Runtime and temporary files should normally be excluded from commits. A suitable
`.gitignore` includes:

```gitignore
__pycache__/
*.py[cod]
*.db
.venv/
```

Excluding `*.db` prevents personal BMI history from being uploaded to GitHub.

## Privacy and medical notice

- Names and BMI records are stored locally as readable SQLite data.
- The application does not provide account security or database encryption.
- Avoid entering sensitive personal information on a shared computer.
- BMI is a general screening measurement, not a medical diagnosis or a
  substitute for professional medical advice.

## References

- [Python Tkinter documentation](https://docs.python.org/3/library/tkinter.html)
- [Python SQLite documentation](https://docs.python.org/3/library/sqlite3.html)
- [Matplotlib documentation](https://matplotlib.org/stable/)
