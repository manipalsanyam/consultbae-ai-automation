ConsultBae — AI Automation Take-Home Assignment

Overview

This repository contains my solution for the ConsultBae AI Automation Take-Home Assignment.

The solution covers the three main implementation tasks:

Consolidating three inconsistent CSV data sources into a clean SQLite database.

Building a working n8n Cloud automation for CSV duplicate detection.

Building a miniature gig-worker audio collection application that stores audio and automatically extracts audio metadata.

It also includes the required data-quality report, stuck log, and scalability note.

Project Structure

consultbae_assignment/
│
├── app/
│   └── audio_app.py
│
├── data/
│   ├── source1_naukri_applicants(1).csv
│   ├── source2_gig_workers(1).csv
│   └── source3_cbnexus_contacts(1).csv
│
├── n8n/
│   └── duplicate_alert.json
│
├── scripts/
│   ├── api.py
│   └── db.py
│
├── storage/
│   └── audio/
│
├── consultbae.db
├── DATA_ISSUES.md
├── SCALE_NOTE.md
├── STUCK_LOG.md
├── requirements.txt
└── README.md

Task 1 — Data Merge and Master Database

Objective

The three supplied CSV files came from different systems and contained overlapping people, inconsistent formatting, and data-quality problems.

The goal was to ingest the three sources into one clean SQLite database and ensure that the same person appearing in multiple sources becomes one master person record.

Approach

The ingestion pipeline is implemented in:

scripts/db.py

The pipeline:

Reads all three CSV files.

Cleans and normalizes fields.

Preserves source-record information.

Attempts conservative identity matching.

Creates a consolidated master-person record.

Stores source provenance separately.

The matching logic prioritizes strong identifiers such as normalized email and phone. Name/city information is used conservatively as supporting evidence rather than blindly merging records based only on a name.

Result

The final ingestion produced:

103 valid source records
        ↓
55 master people

The SQLite database is:

consultbae.db

Main Database Tables

persons

Contains the consolidated master people.

source_records

Preserves source-level records and provenance.

audio_submissions

Stores records created by the audio collection application.

Task 2 — n8n Duplicate Detection Automation

Objective

The assignment requires one working low-code/no-code automation.

I implemented the duplicate-detection option using n8n Cloud.

Workflow

Incoming CSV
     ↓
Receive CSV — Webhook
     ↓
Extract CSV
     ↓
Check Against Master DB
     ↓
Is Duplicate?
    ↙       ↘
  YES       NO
   ↓         ↓
Build      New Person
Alert      Result
   ↓
Respond to Webhook

What the workflow does

Receives a CSV through an n8n webhook.

Extracts the CSV into individual records.

Normalizes incoming identity fields.

Checks each incoming person against the consolidated master dataset.

Routes duplicate records through the duplicate branch.

Returns a duplicate response through the webhook.

The workflow was tested successfully in n8n Cloud using the supplied CSV data.

n8n Export

The workflow export is stored in:

n8n/duplicate_alert.json

Task 3 — Mini Gig-Worker Audio Collection App

Objective

The application provides a simple interface where a worker can:

Enter their name.

Enter their phone number.

Upload an audio recording.

Submit the recording.

View previous submissions.

Play submitted recordings.

Audio Metadata

For every submitted audio file, the application extracts and stores:

Duration

Sample rate

Bitrate

Loudness

Rough quality estimate

The application uses FFmpeg/FFprobe for audio analysis.

Example Successful Submission

One test submission produced:

Duration:      195.744 seconds
Sample rate:   44.1 kHz
Bitrate:       127.623 kbps
Loudness:      -11.5 dB
Quality:       99.93

The submission was successfully stored and displayed with an audio player.

Run the Application

Install dependencies:

pip install -r requirements.txt

Make sure FFmpeg/FFprobe is installed and available on PATH.

Run:

python app/audio_app.py

Then open the local URL shown by the application.

Task 4 — Data Quality Issues

A separate report documents the data-quality problems found while working with the three source files and explains how they were handled.

See:

DATA_ISSUES.md

The focus was not only on cleaning data, but also on documenting potentially unsafe or ambiguous cases instead of silently making assumptions.

Task 5 — Scalability Note

The scalability analysis considers what could fail first if the application were launched to 5,000 gig workers over one weekend.

Topics covered include:

Concurrent uploads

Storage growth

Large audio files

Upload failures

Duplicate submissions

Database contention

Processing bottlenecks

Retry handling

Cost considerations

Object storage

Background processing

See:

SCALE_NOTE.md

Setup

1. Clone the repository

git clone https://github.com/manipalsanyam/consultbae-ai-automation.git
cd consultbae-ai-automation

2. Create a virtual environment

Windows:

python -m venv .venv
.venv\Scripts\activate

macOS/Linux:

python3 -m venv .venv
source .venv/bin/activate

3. Install dependencies

pip install -r requirements.txt

4. Build/refresh the database

python scripts/db.py

Expected result:

103 valid source rows
55 master people

5. Run the audio application

python app/audio_app.py

Running the API

The repository also contains:

scripts/api.py

It provides the local API used during development/testing for database-related checks.

Run:

python scripts/api.py

Health check:

http://127.0.0.1:8000/health

n8n Setup

The n8n workflow is exported in:

n8n/duplicate_alert.json

Import the JSON into n8n.

The current demonstrated workflow uses the n8n Cloud webhook and the duplicate-checking logic contained in the exported workflow.

For testing, use the webhook's Test URL while the webhook is listening for a test event.

Example request:

curl.exe -X POST -F "data=@data/source1_naukri_applicants(1).csv" "YOUR_N8N_TEST_WEBHOOK_URL"

Key Design Decisions

Conservative entity matching

A wrong merge can be more damaging than leaving two possible records separate. Therefore, strong identifiers were prioritized and ambiguous matches were treated conservatively.

Preserve source provenance

Instead of destroying the original source records during cleaning, source-level records are retained separately. This makes the master record explainable and makes debugging easier.

Simple working audio application

The assignment prioritizes working software over visual polish. The audio application therefore focuses on the required workflow and metadata extraction rather than a complex UI.

Low-code automation

The n8n workflow was kept visible and easy to explain because the assignment specifically evaluates the ability to use low-code automation rather than solving Task 2 only with Python.

Testing Performed

The following were tested during development:

CSV ingestion

Master database creation

Consolidation of 103 source records into 55 people

Local API health check

Audio upload

Audio metadata extraction

Audio playback

n8n webhook reception

CSV extraction in n8n

Duplicate matching branch

Duplicate response through the webhook

Known Limitations

This is a take-home assignment implementation rather than a production deployment.

Potential production improvements include:

PostgreSQL instead of SQLite

Object storage for audio

Background audio processing

Authentication and authorization

Rate limiting

Better duplicate-resolution workflows

Structured logging and monitoring

Retry queues

Automated tests

Cloud deployment

Better handling of concurrent uploads

Stuck Log

The detailed development/stuck log is available separately:

STUCK_LOG.md

It records the main places where I got stuck, what I searched or asked AI about, which approaches were tried, and why some approaches were rejected.

Submission

GitHub:

https://github.com/manipalsanyam/consultbae-ai-automation

Demo video:

ADD VIDEO LINK HERE

