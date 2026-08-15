ConsultBae — Development Stuck Log

This document records the main places where I got stuck while completing the assignment, how I investigated them, what I asked AI for help with, and which approaches I rejected.

The goal of this log is to show the actual problem-solving process rather than presenting only the final working solution.

1. Audio Upload Returned “Internal Server Error”

Problem

The audio collection page loaded correctly, but after entering a name and phone number, selecting an audio file, and clicking Submit, the browser returned an Internal Server Error.

The UI itself was working, so the failure appeared to be happening during audio processing.

Initial Investigation

I ran the audio application from the terminal instead of only looking at the browser.

The assignment requires the application to automatically extract:

duration

sample rate

bitrate

loudness

so I suspected the audio-analysis step rather than the HTML form.

What I searched / investigated

I checked how FFmpeg/FFprobe is installed on Windows and how command-line programs are exposed through the Windows PATH environment variable.

I also checked the terminal output rather than assuming that the browser error was the root cause.

AI assistance

I used AI to reason through the likely cause of the server-side error and to identify that FFprobe was required by the audio-processing implementation.

The important lesson was to use the terminal traceback/environment rather than trying to fix the browser page itself.

What I initially tried

I first tested:

ffprobe -version

Windows returned that ffprobe was not recognized.

Root Cause

FFmpeg/FFprobe was not available in the Windows PATH.

The first FFmpeg download also did not contain the expected bin directory because it was not the ready-to-run Windows build I needed.

Solution

I downloaded a Windows FFmpeg build containing:

bin/
    ffmpeg.exe
    ffprobe.exe

I then added the bin directory to the Windows PATH and restarted VS Code.

After restarting,:

ffprobe -version

worked successfully.

Verification

The audio application then successfully processed a real test recording and displayed:

Duration:      195.744 seconds
Sample rate:   44.1 kHz
Bitrate:       127.623 kbps
Loudness:      -11.5 dB
Quality:       99.93

The recording was also playable from the submissions view.

What I rejected

I considered changing the application to avoid FFmpeg entirely, but the existing FFmpeg/FFprobe approach was more reliable for extracting the required metadata. I therefore fixed the environment instead of unnecessarily rewriting the audio-processing implementation.

2. n8n Cloud Could Not Reach the Local API

Problem

The n8n workflow was originally designed to call:

http://127.0.0.1:8000/duplicate-check

The local API worked correctly from the laptop.

However, the n8n instance was running on n8n Cloud.

This created a networking problem: 127.0.0.1 from n8n Cloud refers to the n8n Cloud environment, not my laptop.

Investigation

I first verified the local API independently.

Running:

python scripts/api.py

and opening:

http://127.0.0.1:8000/health

returned:

{"ok": true}

Therefore the API itself was not broken.

The problem was connectivity between n8n Cloud and the local machine.

AI assistance

I asked AI why the local API was not reachable from n8n Cloud.

The explanation was that a cloud-hosted service cannot directly access a laptop's localhost.

Approach considered: ngrok

The first solution proposed was to expose port 8000 using ngrok.

The intended architecture was:

n8n Cloud
   ↓
ngrok public URL
   ↓
localhost:8000
   ↓
api.py

Why I rejected it

When I attempted to use ngrok, the installation required authentication.

More importantly, introducing a public tunnel added infrastructure that was not actually necessary for the assignment.

The assignment requires the n8n automation to be connected to the data and to demonstrate duplicate detection; it does not require a public tunnel or a local API to be exposed to the internet.

Final approach

I changed the n8n approach so that the Cloud workflow could perform the duplicate check using the master data available to the workflow instead of depending on my laptop's localhost API.

This reduced the number of moving parts:

CSV
 ↓
n8n Cloud
 ↓
Extract CSV
 ↓
Master-data duplicate matching
 ↓
Duplicate branch
 ↓
Webhook response

Lesson

The important debugging step was separating:

“Is my API working?”

“Can the cloud service reach my API?”

The API was working; the network boundary was the real problem.

3. n8n CSV Extraction Node Failed After Import

Problem

After importing the workflow JSON into n8n Cloud, the Webhook successfully received the CSV.

However, the Extract CSV node initially failed.

The node contained an imported operation value that was not valid for the current n8n node version.

The error was effectively an invalid/unsupported CSV extraction operation.

Investigation

I checked the node configuration rather than assuming the uploaded CSV was corrupt.

The Webhook node showed that the file had been received as binary data under:

data

Therefore the upload itself was working.

AI assistance

I used AI to reason about the n8n node-version mismatch and to identify that the imported JSON's operation value did not match the available operation in the current n8n UI.

Solution

I opened the Extract From File node and selected the correct CSV extraction operation from the current n8n UI instead of relying on the imported operation value.

The binary property remained:

data

Verification

After changing the operation, the node successfully produced:

42 items

from the test CSV.

The downstream duplicate-checking branch then executed successfully.

What I rejected

I did not replace the n8n workflow with a Python-only implementation.

That would have undermined the purpose of Task 2 because the assignment explicitly requires a no-code/low-code tool and says pure-code solutions for that task score zero.

4. PowerShell Quoting Caused SQLite Verification Errors

Problem

While verifying the database from PowerShell, I initially used Python one-liners containing nested SQL quotes.

Commands such as:

SELECT name FROM sqlite_master WHERE type='table'

were repeatedly broken by PowerShell/Python quote handling.

This produced errors such as:

SyntaxError: unterminated string literal

and:

sqlite3.OperationalError: near "table": syntax error

Investigation

The ingestion script had already printed:

Ingested 103 valid source rows into 55 master people.

So I knew the database generation had succeeded.

The verification command was the failing component.

I also initially queried a table named:

people

but the actual table created by the project was:

persons

which produced:

sqlite3.OperationalError: no such table: people

Solution

I stopped using the complicated table-listing SQL and used a simpler direct count:

python -c "import sqlite3; c=sqlite3.connect('consultbae.db'); print(c.execute('select count(*) from persons').fetchone()[0])"

This returned:

55

I then verified the source-record count and got:

103

Lesson

The underlying database was working. The mistake was in the verification command and table-name assumption.

When debugging, I learned to separate:

database generation

from:

database verification command

rather than treating every command-line error as a database failure.

5. GitHub Push Failed Because There Was No Commit

Problem

After initializing Git and trying:

git push -u origin main

Git returned:

error: src refspec main does not match any

Investigation

The repository had been initialized, but there were no commits yet.

The local files were staged, but a branch with a commit could not be pushed before creating the initial commit.

Solution

I staged the project:

git add .

then created the initial commit:

git commit -m "feat: complete ConsultBae assignment"

and pushed:

git push -u origin main

The final local branch became:

main

and the remote tracking branch became:

origin/main

Final verification

git log --oneline --decorate -5

showed:

fb4e436 (HEAD -> main, origin/main) feat: complete ConsultBae assignment

Lesson

Git initialization, staging, committing, and pushing are separate steps. A remote repository can exist while the local repository still has nothing to push.

6. General Problem-Solving Pattern I Used

Across the problems above, the most useful debugging pattern was:

Step 1 — Reproduce

Run the failing command or workflow again.

Step 2 — Identify the exact boundary

Determine whether the failure is:

browser/UI

Python application

external executable

database

n8n node

network

Git

PowerShell syntax

Step 3 — Verify the smallest component

Examples:

ffprobe -version

for FFmpeg,

/health

for the API,

and direct SQLite counts for the database.

Step 4 — Change one thing

Instead of changing multiple parts at once, I changed the specific failing component.

Step 5 — Re-run the complete flow

After fixing the component, I tested the end-to-end flow again.

This helped avoid confusing one problem with another.

Final Outcome

After working through these issues, the following parts were successfully demonstrated:

3 CSV sources ingested

103 source records consolidated into 55 master people

SQLite master database created

n8n Cloud webhook receiving CSV data

CSV extraction working

Duplicate matching branch working

Duplicate response returned through webhook

Audio upload working

Audio metadata extraction working

Audio playback working

Data issues documented

Scalability considerations documented

Project pushed to GitHub

The main remaining submission work is the short screen recording and final repository/video links.