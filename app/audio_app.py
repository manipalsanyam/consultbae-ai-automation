import os, sqlite3, subprocess, json, tempfile, re, math
from pathlib import Path
from flask import Flask, request, redirect, url_for, render_template_string, send_file
from werkzeug.utils import secure_filename

DB=os.getenv("CONSULTBAE_DB","consultbae.db")
AUDIO_DIR=Path(os.getenv("AUDIO_DIR","storage/audio")); AUDIO_DIR.mkdir(parents=True,exist_ok=True)
app=Flask(__name__)
HTML="""<!doctype html><title>ConsultBae Audio Collector</title>
<h1>Gig Audio Collection</h1>
<form method=post enctype=multipart/form-data>
<label>Name <input name=name required></label><br><br>
<label>Phone <input name=phone required></label><br><br>
<label>Audio <input type=file name=audio accept=audio/* required></label><br><br>
<button>Submit</button></form>
<hr><h2>Submissions</h2>
{% for x in rows %}<div style="margin:16px 0"><b>{{x[1]}}</b> — {{x[2]}}
<audio controls preload="metadata" src="{{ url_for('audio', name=x[4]) }}"></audio>
<pre>duration={{x[5]}}s | sample_rate={{x[6]}} kHz | bitrate={{x[7]}} kbps | loudness={{x[8]}} dB | quality={{x[9]}}</pre></div>{% endfor %}"""

def ffprobe(path):
    cmd=["ffprobe","-v","error","-show_entries","format=duration:stream=sample_rate,bit_rate",
         "-of","json",str(path)]
    out=subprocess.check_output(cmd,text=True); d=json.loads(out)
    fmt=d.get("format",{}); st=(d.get("streams") or [{}])[0]
    duration=float(fmt.get("duration") or 0)
    sr=float(st.get("sample_rate") or 0)
    br=float(st.get("bit_rate") or 0)/1000
    return duration,sr/1000,br

def loudness(path):
    # EBU-style integrated loudness is not attempted; RMS converted to dBFS is a useful rough proxy.
    cmd=["ffmpeg","-i",str(path),"-af","volumedetect","-f","null","-"]
    p=subprocess.run(cmd,text=True,capture_output=True)
    m=re.search(r"mean_volume:\s*(-?[\d.]+)\s*dB",p.stderr)
    return float(m.group(1)) if m else None

def person_id(name,phone_number):
    con=sqlite3.connect(DB); ph=re.sub(r"\D","",phone_number)[-10:]
    row=con.execute("SELECT person_id FROM persons WHERE phone=? LIMIT 1",(ph,)).fetchone()
    if not row:
        row=con.execute("SELECT person_id FROM persons WHERE replace(lower(canonical_name),' ','')=? LIMIT 1",
                         (re.sub(r"[^a-z0-9]","",name.lower()),)).fetchone()
    con.close(); return row[0] if row else None

@app.post("/")
def submit():
    name=request.form["name"]; ph=request.form["phone"]; f=request.files["audio"]
    fn=secure_filename(f.filename); path=AUDIO_DIR/f"{os.urandom(8).hex()}_{fn}"; f.save(path)
    duration,srk,br=ffprobe(path); loud=loudness(path)
    # Simple 0-100 heuristic: duration, sample rate, bitrate, and non-silent audio.
    q=0
    q += min(duration/3,1)*20
    q += min(srk/44.1,1)*25
    q += min(br/128,1)*25
    q += max(0,min(1,(60+abs(loud or -60))/60))*30
    con=sqlite3.connect(DB)
    con.execute("""INSERT INTO audio_submissions(person_id,name,phone,file_path,duration_seconds,
      sample_rate_khz,bitrate_kbps,loudness_db,quality_score) VALUES(?,?,?,?,?,?,?,?,?)""",
      (person_id(name,ph),name,ph,str(path),duration,srk,br,loud,q))
    con.commit(); con.close(); return redirect(url_for("home"))

@app.get("/")
def home():
    con=sqlite3.connect(DB)
    rows=con.execute("""SELECT id,name,phone,file_path,replace(file_path,'storage/audio/',''),
      duration_seconds,sample_rate_khz,bitrate_kbps,loudness_db,quality_score
      FROM audio_submissions ORDER BY id DESC""").fetchall(); con.close()
    return render_template_string(HTML,rows=rows)

@app.get("/audio/<path:name>")
def audio(name):
    file_path = AUDIO_DIR / name

    if not file_path.exists():
        return "Audio file not found", 404

    return send_file(
        file_path,
        mimetype="audio/mpeg",
        as_attachment=False
    )

if __name__=="__main__": app.run(host="0.0.0.0",port=8501)
