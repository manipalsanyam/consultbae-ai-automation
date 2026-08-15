# ConsultBae — AI Automation Take-Home

A working submission for the five-part assignment: messy CSV merge, one n8n automation, an audio collection app, a data-quality report, and a scale-up note.

## What is included

- `scripts/db.py` — ingests all 3 CSVs into SQLite and performs deterministic entity resolution.
- `consultbae.db` — generated SQLite database.
- `scripts/api.py` — tiny API used by the n8n workflow to check a person against the merged database.
- `app/audio_app.py` — upload-based audio collection web app. Browser recording is not required by the brief; upload is sufficient.
- `n8n/duplicate_alert.json` — importable n8n workflow: CSV webhook → CSV parsing → duplicate check → alert.
- `DATA_ISSUES.md` — specific issues found and handling decisions.
- `STUCK_LOG.md` — realistic decision/debug log.
- `SCALE_NOTE.md` — optional 5,000-worker weekend launch plan.

The assignment explicitly prioritizes working software, sensible matching, data issues caught, and the ability to explain decisions. fileciteturn0file0L14-L27

## Quick start

### 1. Install

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

`ffmpeg` and `ffprobe` must also be available on PATH for audio metadata extraction.

### 2. Build the merged database

```bash
python scripts/db.py
```

Expected result with the supplied files:

```text
Ingested 103 valid source rows into 55 master people.
```

The ingestion:
1. normalizes email, phone, name and city;
2. removes obvious non-data rows;
3. links exact normalized email or phone first;
4. uses exact normalized name + normalized city only when that match is unambiguous within each source;
5. preserves every source row in `source_records` instead of deleting evidence;
6. stores a canonical person in `persons`.

This avoids using fuzzy name similarity as the final merge key, which would incorrectly merge people such as Isha Chopra/Sneha Chopra or two Arjun Mehta records.

### 3. Run the duplicate-check API

Terminal 1:

```bash
python scripts/api.py
```

Health check:

```bash
curl http://localhost:8000/health
```

Test:

```bash
curl -X POST http://localhost:8000/duplicate-check ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Tanvi Gupta\",\"email\":\"tanvi.gupta31@example.com\",\"phone\":\"9000000254\"}"
```

### 4. Run the audio app

Terminal 2:

```bash
python app/audio_app.py
```

Open `http://localhost:8501`.

Enter name + phone, upload an audio file, and submit. The app stores:
- duration in seconds
- sample rate in kHz
- bitrate in kbps
- loudness as an approximate dBFS/RMS proxy
- a simple quality score

The assignment asks for these four extracted properties and a second listing view with playback. fileciteturn0file0L28-L39

### 5. n8n automation

Use a self-hosted n8n instance. Import:

`n8n/duplicate_alert.json`

Flow:

**Webhook (CSV upload) → Spreadsheet File parser → Split Rows → HTTP duplicate check → IF duplicate → Email alert**

The assignment requires one working no-code/low-code automation and an exported flow JSON. fileciteturn0file0L18-L27

Before testing:
- change the duplicate-check URL if n8n is not running in Docker;
- set a real alert email;
- configure SMTP credentials;
- make sure the API is reachable from the n8n container (`host.docker.internal` works in Docker Desktop; on Linux use the host gateway or a shared Docker network).

### 6. GitHub

```bash
git init
git add .
git commit -m "feat: initial ConsultBae assignment solution"
git add .
git commit -m "feat: add data quality report and automation"
git add .
git commit -m "feat: add audio collection app"
```

Push to a private/public repo as requested by the recruiter. The assignment specifically says they inspect commit history. fileciteturn0file0L46-L55

## 6-minute demo script

1. **0:00–0:45 — Merge**
   - Run `python scripts/db.py`.
   - Show the `55 master people` result.
   - Explain exact email/phone first, then conservative name+city matching.

2. **0:45–2:00 — Data quality**
   - Open `DATA_ISSUES.md`.
   - Point out duplicate rows, malformed row, header row, mixed formats, future dates, unit inconsistencies and conflicting identifiers.

3. **2:00–3:15 — n8n**
   - Show imported workflow.
   - POST a CSV through the webhook.
   - Show duplicate branch and alert.

4. **3:15–5:15 — Audio**
   - Open app.
   - Enter a known person.
   - Upload a short `.wav`/`.mp3`.
   - Submit.
   - Show duration, sample rate, bitrate, loudness, quality and playback.

5. **5:15–6:00 — Hard decisions**
   - Explain why fuzzy names were not used as an automatic merge key.
   - Explain the duplicate/ambiguous records and how source evidence is retained.
   - Mention what you would change for 5,000 workers.

The assignment says voice is required in the screen recording but face is not. fileciteturn0file0L53-L54

## Important honesty note

Do not claim the n8n workflow is cloud-hosted or that an external deployment exists if you only demonstrate it locally. The assignment accepts local execution in the video. fileciteturn0file0L37-L39

Also be able to explain every line: the assignment explicitly says shortlisted candidates may extend the solution live. fileciteturn0file0L56-L59
