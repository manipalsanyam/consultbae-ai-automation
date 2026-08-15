# Stretch — 5,000 Workers in One Weekend

The first things likely to break are not the HTML form itself; they are file storage, concurrent uploads, database writes, duplicate submissions, and operational observability.

## Before launch

1. **Object storage instead of local disk**
   - Store audio in S3-compatible object storage.
   - Store only the object key and metadata in Postgres.
   - Add lifecycle rules for temporary uploads.

2. **Upload limits and validation**
   - Enforce maximum file size.
   - Allow only supported audio MIME types/extensions.
   - Reject corrupted files and extremely long recordings.
   - Consider direct-to-object-storage uploads so the app server does not proxy every audio byte.

3. **Async metadata processing**
   - Upload → create submission row → queue a metadata job.
   - Workers run ffprobe/FFmpeg and update duration, sample rate, bitrate and loudness.
   - This prevents a slow FFmpeg process from blocking web requests.

4. **Database**
   - Move from SQLite to managed Postgres.
   - Add unique/idempotency keys for submissions.
   - Index normalized phone/email and submission status.

5. **Duplicate protection**
   - Generate an upload/request idempotency key.
   - Avoid storing the same recording twice after retries.
   - Keep source records and submission records separate.

6. **Reliability**
   - Queue failed processing jobs for retry.
   - Dead-letter permanently failing files.
   - Add structured logs and basic metrics: upload success rate, processing latency, queue depth, error rate and storage growth.

7. **Cost controls**
   - Estimate average audio size × 5,000 before launch.
   - Compress/normalize only if the project requirements permit it.
   - Add retention rules and monitor storage/egress.

8. **Security**
   - Validate file contents, not only extensions.
   - Never execute uploaded files.
   - Rate-limit the form.
   - Use HTTPS and avoid exposing object storage credentials to the browser.

The assignment specifically asks what breaks first and what should change before a 5,000-worker weekend, with attention to storage, uploads, failures, duplicates and cost. fileciteturn0file0L43-L45
