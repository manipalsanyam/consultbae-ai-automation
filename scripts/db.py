import csv, re, sqlite3, argparse, os
from pathlib import Path
from collections import defaultdict

DB_PATH = Path(os.getenv("CONSULTBAE_DB", "consultbae.db"))
DATA_DIR = Path(os.getenv("CONSULTBAE_DATA", "data"))

def norm_text(v):
    return re.sub(r"[^a-z0-9]", "", str(v or "").strip().lower())

def norm_email(v):
    return str(v or "").strip().lower()

def norm_phone(v):
    digits = re.sub(r"\D", "", str(v or ""))
    return digits[-10:] if len(digits) >= 10 else digits

def norm_city(v):
    s = str(v or "").strip().lower()
    aliases = {"gurgaon":"gurgaon","gurugram":"gurgaon","new delhi":"delhi",
               "delhi ncr":"delhi","bangalore":"bengaluru","bengaluru":"bengaluru"}
    return aliases.get(s, s)

def parse_source(path, source):
    rows=[]
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row_no, r in enumerate(csv.DictReader(f), start=2):
            if source == "naukri":
                name, email, phone, city = r["Full Name"], r["Email"], r["Phone"], r["City"]
                skills=r["Skills"]
                extra={"experience":r["Experience (Years)"],"ctc":r["Current CTC"],"applied_date":r["Applied Date"]}
            elif source == "gig":
                # One planted row is shifted by one column. Detect it by an email-like
                # worker_name plus a comma-separated value in the email column.
                if "@" in str(r["worker_name"]) and "," in str(r["email_id"]):
                    email, name = r["worker_name"], r["rate"]
                    rate, city, status, skills = r["location"], r["status"], r["skill_tags"], r["email_id"]
                else:
                    name, email, phone, city = r["worker_name"], r["email_id"], "", r["location"]
                    rate, status, skills = r["rate"], r["status"], r["skill_tags"]
                phone=""
                extra={"rate":rate,"status":status}
            else:
                name, email, phone, city = r["Name"], "", r["Phone Number"], r["City"]
                skills=""; extra={"verified":r["Verified"],"projects_completed":r["Projects Completed"]}
            if not norm_text(name) or norm_text(name) in {"name"}:
                continue
            rec={"source":source,"source_row":row_no,"name":name,"email":email,"phone":phone,
                 "city":city,"skills":skills or "", "nname":norm_text(name),
                 "nemail":norm_email(email),"nphone":norm_phone(phone),
                 "ncity":norm_city(city)}
            rec.update(extra)
            rows.append(rec)
    return rows

def load_all():
    return (parse_source(DATA_DIR/"source1_naukri_applicants(1).csv","naukri") +
            parse_source(DATA_DIR/"source2_gig_workers(1).csv","gig") +
            parse_source(DATA_DIR/"source3_cbnexus_contacts(1).csv","cbnexus"))

def cluster(records):
    parent=list(range(len(records)))
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b: parent[b]=a
    emailmap={}; phonemap={}
    for i,r in enumerate(records):
        if r["nemail"]:
            if r["nemail"] in emailmap: union(i,emailmap[r["nemail"]])
            else: emailmap[r["nemail"]]=i
        if r["nphone"]:
            if r["nphone"] in phonemap: union(i,phonemap[r["nphone"]])
            else: phonemap[r["nphone"]]=i
    # Exact normalized name + normalized city is used only when it is unambiguous
    # within each source. This links records where one source has no common ID.
    key_roots=defaultdict(set)
    for i,r in enumerate(records):
        key_roots[(r["nname"],r["ncity"])].add(find(i))
    for key, roots in key_roots.items():
        if len(roots) <= 1: continue
        roots=list(roots)
        base=roots[0]
        base_srcs={records[j]["source"] for j in range(len(records)) if find(j)==base}
        if sum(1 for j in range(len(records)) if find(j)==base and records[j]["source"] in base_srcs) < len(base_srcs):
            pass
        for root in roots[1:]:
            root_srcs=[records[j]["source"] for j in range(len(records)) if find(j)==root]
            root_set=set(root_srcs)
            # Merge only if neither cluster contains two rows from the same source
            # and their source sets do not overlap.
            if len(root_srcs)==len(root_set) and not (base_srcs & root_set):
                union(base,root)
                base_srcs |= root_set
    groups=defaultdict(list)
    for i in range(len(records)): groups[find(i)].append(i)
    return list(groups.values())

def init_db(conn):
    conn.executescript("""
    PRAGMA foreign_keys=ON;
    CREATE TABLE IF NOT EXISTS persons(
      person_id TEXT PRIMARY KEY,
      canonical_name TEXT NOT NULL,
      email TEXT,
      phone TEXT,
      city TEXT,
      skills TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS source_records(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      person_id TEXT NOT NULL REFERENCES persons(person_id),
      source TEXT NOT NULL,
      source_row INTEGER NOT NULL,
      raw_name TEXT, raw_email TEXT, raw_phone TEXT, raw_city TEXT,
      normalized_email TEXT, normalized_phone TEXT,
      raw_payload TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS audio_submissions(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      person_id TEXT REFERENCES persons(person_id),
      name TEXT NOT NULL, phone TEXT NOT NULL,
      file_path TEXT NOT NULL, duration_seconds REAL,
      sample_rate_khz REAL, bitrate_kbps REAL, loudness_db REAL,
      quality_score REAL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_sr_email ON source_records(normalized_email);
    CREATE INDEX IF NOT EXISTS idx_sr_phone ON source_records(normalized_phone);
    CREATE INDEX IF NOT EXISTS idx_person_phone ON persons(phone);
    CREATE INDEX IF NOT EXISTS idx_person_email ON persons(email);
    """)

def choose(cands, key):
    return next((str(c.get(key,"")) for c in cands if str(c.get(key,"")).strip()), "")

def ingest():
    records=load_all(); groups=cluster(records)
    conn=sqlite3.connect(DB_PATH); init_db(conn)
    conn.execute("DELETE FROM source_records"); conn.execute("DELETE FROM persons")
    for n, idxs in enumerate(groups, start=1):
        rs=[records[i] for i in idxs]
        # Prefer Naukri as the richest canonical source.
        ranked=sorted(rs, key=lambda r: (r["source"]!="naukri", r["source"]=="gig"))
        c=ranked[0]
        skills=[]
        for r in rs:
            for s in re.split(r",\s*", r.get("skills","")):
                s=s.strip().lower()
                if s and s not in skills: skills.append(s)
        pid=f"CB-{n:04d}"
        conn.execute("INSERT INTO persons(person_id,canonical_name,email,phone,city,skills) VALUES(?,?,?,?,?,?)",
                     (pid,c["name"],choose(rs,"nemail"),choose(rs,"nphone"),c["city"],", ".join(skills)))
        for r in rs:
            conn.execute("""INSERT INTO source_records
              (person_id,source,source_row,raw_name,raw_email,raw_phone,raw_city,normalized_email,normalized_phone,raw_payload)
              VALUES(?,?,?,?,?,?,?,?,?,?)""",
              (pid,r["source"],r["source_row"],r["name"],r["email"],r["phone"],r["city"],
               r["nemail"],r["nphone"],repr(r)))
    conn.commit()
    print(f"Ingested {len(records)} valid source rows into {len(groups)} master people.")
    conn.close()

if __name__=="__main__":
    ingest()
