# Stuck Log

The assignment asks for specific examples of where I got stuck and how I got unstuck.

## 1. Deciding whether similar names were the same person

**Problem:** Several names are close enough that a fuzzy matcher would return a high score. For example, Isha Chopra and Sneha Chopra share a surname and similar spelling. There are also two Arjun Mehta records with different phone numbers.

**What I searched/considered:** I checked normalized names, phone numbers, email addresses and city values across all three CSVs. I considered using fuzzy string matching.

**What I rejected:** I rejected automatic fuzzy-name merging because a high name score does not prove identity.

**Solution:** I made exact normalized email/phone the primary keys and only allow exact name+city matching when it is unambiguous within each source. Ambiguous records stay separate.

## 2. The CBNexus CSV contains a header row in the middle

**Problem:** Row 15 contains the column headers as data.

**How I found it:** A quick inspection showed `Name`, `Phone Number`, `City`, `Verified`, `Projects Completed` appearing as a normal row.

**Solution:** The ingestion checks for the normalized name `name` and skips that row. This is also documented in the data-quality report.

## 3. Audio metadata extraction

**Problem:** Duration, sample rate, bitrate and loudness are not reliably available from the filename alone.

**What I searched:** I checked common Python audio approaches and the available command-line media tooling.

**Solution:** I used `ffprobe` for duration/sample-rate/bitrate and FFmpeg's `volumedetect` mean-volume output as a practical loudness proxy. The app labels the result as a rough dBFS/RMS-style measurement rather than pretending it is a calibrated acoustic dB measurement.

## AI usage

AI was used as a coding/reasoning assistant to help structure the pipeline, identify edge cases and draft implementation ideas. The final decisions above were checked against the supplied CSVs and assignment requirements. I would be able to explain the matching and audio-extraction logic in a live review.
