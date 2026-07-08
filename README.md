# Sauce Labs Visual Test — Home Page vs. Figma Design

This guide walks you through running an automated visual test. The script logs in to the
Sustainability Portal, takes a picture ("snapshot") of the Home Page in a browser running on
Sauce Labs, and compares it against your **Figma design** to catch any visual differences.

**You do not need to be a programmer to run this.** Follow the steps in order and copy/paste
the commands exactly. Every command is shown for both **Mac** and **Windows** — use the ones
that match your computer.

---

## Contents

1. [What you need before you start](#1-what-you-need-before-you-start)
2. [Install Python](#2-install-python)
3. [Put the files in a folder](#3-put-the-files-in-a-folder)
4. [Open a terminal in that folder](#4-open-a-terminal-in-that-folder)
5. [Set up the Python environment](#5-set-up-the-python-environment)
6. [Install the required packages](#6-install-the-required-packages)
7. [Get your Sauce Labs credentials](#7-get-your-sauce-labs-credentials)
8. [Enter (export) your credentials](#8-enter-export-your-credentials)
9. [Run the test](#9-run-the-test)
10. [See the results](#10-see-the-results)
11. [Troubleshooting](#11-troubleshooting)
12. [Quick reference (for repeat runs)](#12-quick-reference-for-repeat-runs)
13. [Settings you can change](#13-settings-you-can-change)

---

## 1. What you need before you start

- A **Mac or Windows computer**.
- A **Sauce Labs account** with Visual Testing turned on. (Ask your Sauce Labs contact if
  you're not sure.)
- The Figma design has already been **exported to Sauce Labs** (this was set up for you —
  you don't need to do anything with Figma).
- **Internet access** to the portal at `https://sportal-npd.ct-costco.com/`. If your company
  requires a VPN to reach that site, connect to it first.
- The two files that came with this guide:
  - `sauce_visual_figma_test.py` — the test.
  - `requirements.txt` — the list of software the test needs.

A "terminal" is just a text window where you type commands. On **Mac** it's called
**Terminal**; on **Windows** it's called **PowerShell**. Don't worry — this guide tells you
exactly what to type.

---

## 2. Install Python

Python is the software that runs the test. You may already have it.

### Check if you already have it

Open a terminal (see [Step 4](#4-open-a-terminal-in-that-folder) if you're not sure how) and type:

**Mac:**
```bash
python3 --version
```

**Windows:**
```powershell
python --version
```

If you see something like `Python 3.10.6` (any 3.8 or higher is fine), you're set — skip to
[Step 3](#3-put-the-files-in-a-folder).

### If it's not installed

1. Go to <https://www.python.org/downloads/>.
2. Click the big **Download Python** button and run the installer.
3. **Windows only, very important:** on the first screen of the installer, check the box that
   says **"Add Python to PATH"** before clicking Install. If you miss this, the commands below
   won't work.
4. Finish the installer, then close and reopen your terminal and run the version check above
   again to confirm.

---

## 3. Put the files in a folder

Create a folder somewhere easy to find (for example, on your Desktop) and put both files
inside it:

- `sauce_visual_figma_test.py`
- `requirements.txt`

Name the folder something simple like `SauceVisualTest`. Keep both files together in this
same folder.

---

## 4. Open a terminal in that folder

You want your terminal "pointed at" the folder from Step 3.

### Mac

1. Open the **Terminal** app (press `Cmd + Space`, type `Terminal`, press Enter).
2. Type `cd ` (the letters c, d, and a space) — **do not press Enter yet**.
3. Drag the `SauceVisualTest` folder from Finder onto the Terminal window. It will fill in the
   folder location for you.
4. Press **Enter**.

### Windows

1. Open **File Explorer** and go into the `SauceVisualTest` folder.
2. Click in the address bar at the top, type `powershell`, and press **Enter**.
   A PowerShell window opens already pointed at that folder.

To confirm you're in the right place, list the files:

**Mac:**
```bash
ls
```

**Windows:**
```powershell
dir
```

You should see `sauce_visual_figma_test.py` and `requirements.txt` listed. If you don't, you're
in the wrong folder — repeat this step.

---

## 5. Set up the Python environment

This creates a private, self-contained space for the test's software so it doesn't interfere
with anything else on your computer. You only do this **once** per folder.

**Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

After this, your terminal line will start with `(.venv)`. That means the environment is
**active**. You'll need it active every time you run the test (see the
[Quick reference](#12-quick-reference-for-repeat-runs)).

> **Windows note:** if you see a red error mentioning "running scripts is disabled on this
> system," run this once, then try the activate command again:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```
> Answer `Y` if it asks.

---

## 6. Install the required packages

With `(.venv)` showing, install the software the test needs:

**Mac:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Windows:**
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

This downloads two packages (`saucelabs_visual` and `selenium`). It may take a minute. You
only need to do this **once** per folder. You do **not** need to install a browser — the
browser runs on Sauce Labs' servers.

---

## 7. Get your Sauce Labs credentials

The test signs in to Sauce Labs using two values tied to your account:

- **Username**
- **Access Key**

To find them:

1. Sign in at <https://app.saucelabs.com/>.
2. Go to <https://app.saucelabs.com/user-settings>.
3. Copy your **Username** and your **Access Key**. (The Access Key is hidden by default —
   click the reveal/copy icon next to it.)

Treat your Access Key like a password. Don't share it or post it anywhere public.

You also need your **Region** — the Sauce Labs data center your account uses. It is one of:
`us-west-1`, `us-east-4`, or `eu-central-1`. **It must be the same region the Figma design was
exported to.** If you're unsure, ask your Sauce Labs contact; most US accounts use `us-west-1`.

---

## 8. Enter (export) your credentials

"Exporting" just means telling this terminal window your credentials so the test can use them.
Replace the example values with your real ones from Step 7. Keep the quotation marks.

**Mac:**
```bash
export SAUCE_USERNAME="your-sauce-username"
export SAUCE_ACCESS_KEY="your-sauce-access-key"
export SAUCE_REGION="us-west-1"
```

**Windows:**
```powershell
$env:SAUCE_USERNAME="your-sauce-username"
$env:SAUCE_ACCESS_KEY="your-sauce-access-key"
$env:SAUCE_REGION="us-west-1"
```

**Important:** these values only last as long as the terminal window stays open. If you close
it, you'll need to run these three lines again next time (see the
[Quick reference](#12-quick-reference-for-repeat-runs)).

---

## 9. Run the test

Make sure of two things first: your terminal line still starts with `(.venv)`, and — if the
portal needs a VPN — that your VPN is connected. Then run:

**Mac:**
```bash
python sauce_visual_figma_test.py
```

**Windows:**
```powershell
python sauce_visual_figma_test.py
```

The test will:

1. Start a Chrome browser on Sauce Labs.
2. Open the portal and sign in.
3. Wait a few seconds for the Home Page images to load.
4. Take a snapshot and compare it to the Figma design.
5. Finish.

When it's done, the terminal returns to a normal prompt with no error message. That's success.

---

## 10. See the results

1. Go to the Sauce Labs Visual dashboard: <https://app.saucelabs.com/visual/builds/>
2. Find the build named **`SVP-POC`** on the **`Demo`** branch.
3. Open it to see the **Home Page** snapshot compared against the Figma design. Any visual
   differences are highlighted, and you can approve or reject them from there.

---

## 11. Troubleshooting

**"command not found: python3" (Mac) or "python is not recognized" (Windows)**
Python isn't installed or (on Windows) wasn't added to PATH. Redo [Step 2](#2-install-python)
and make sure to check **"Add Python to PATH"** on Windows.

**My terminal line doesn't start with `(.venv)`**
The environment isn't active. Re-run the `activate` command from [Step 5](#5-set-up-the-python-environment).
On Windows that's `.\.venv\Scripts\Activate.ps1`; on Mac it's `source .venv/bin/activate`.

**"Could not open requirements file"**
Your terminal isn't in the folder with the files. Redo [Step 4](#4-open-a-terminal-in-that-folder),
then check with `ls` (Mac) or `dir` (Windows) that you can see the two files.

**"KeyError: 'SAUCE_USERNAME'"**
You didn't enter your credentials in this terminal window. Redo [Step 8](#8-enter-export-your-credentials).

**A sign-in or authentication error from Sauce Labs**
Double-check the Username and Access Key are correct, and that `SAUCE_REGION` matches your
account's region.

**"No baseline to compare against" / the snapshot shows up as brand new**
The `SAUCE_REGION` or branch doesn't match where the Figma design was exported. Confirm the
region with your Sauce Labs contact.

**The page can't be reached / the test hangs on loading**
You may need to connect to your company VPN before running the test.

**The snapshot looks like it was taken before images finished loading**
Increase the wait time — see [Settings you can change](#13-settings-you-can-change).

If you get stuck, copy the full text the terminal printed (especially anything in red or the
lines starting with `Traceback`) and send it to your technical contact.

---

## 12. Quick reference (for repeat runs)

Once everything is installed, running the test again is quick. Open a terminal in the folder
([Step 4](#4-open-a-terminal-in-that-folder)) and run:

**Mac:**
```bash
source .venv/bin/activate
export SAUCE_USERNAME="your-sauce-username"
export SAUCE_ACCESS_KEY="your-sauce-access-key"
export SAUCE_REGION="us-west-1"
python sauce_visual_figma_test.py
```

**Windows:**
```powershell
.\.venv\Scripts\Activate.ps1
$env:SAUCE_USERNAME="your-sauce-username"
$env:SAUCE_ACCESS_KEY="your-sauce-access-key"
$env:SAUCE_REGION="us-west-1"
python sauce_visual_figma_test.py
```

You do **not** need to recreate the environment or reinstall packages — just activate, enter
credentials, and run.

---

## 13. Settings you can change

If you ever need to adjust the test, open `sauce_visual_figma_test.py` in a plain text editor.
The settings are grouped at the top of the file:

| Setting | What it controls |
| --- | --- |
| `APP_URL`, `APP_USERNAME`, `APP_PASSWORD` | The portal address and the login used to sign in. |
| `POST_LOGIN_WAIT_SECONDS` | How many seconds to wait after login for images to load (currently `5`). Increase this if the Home Page loads slowly. |
| `SNAPSHOT_NAME`, `TEST_NAME`, `SUITE_NAME`, `BUILD_BRANCH` | Labels that must match the Figma design's settings so the comparison lines up. Don't change these unless the Figma export changed. |

**Advanced / for support:** running `DEBUG_DUMP=1 python sauce_visual_figma_test.py` prints a
list of the login page's fields and buttons. This is only useful if the login page changes and
a technical contact needs to update the script.
