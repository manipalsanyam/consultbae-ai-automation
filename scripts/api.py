from flask import Flask, request, jsonify
import sqlite3, os, re
app=Flask(__name__)
DB=os.getenv("CONSULTBAE_DB","consultbae.db")

def norm(v): return re.sub(r"[^a-z0-9]","",str(v or "").lower())
def phone(v):
    d=re.sub(r"\D","",str(v or "")); return d[-10:] if len(d)>=10 else d

@app.post("/duplicate-check")
def duplicate_check():
    p=request.get_json(force=True)
    email=str(p.get("email","")).strip().lower()
    ph=phone(p.get("phone",""))
    name=norm(p.get("name",""))
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
    rows=con.execute("""SELECT p.* FROM persons p
      WHERE (?<>'' AND lower(coalesce(p.email,''))=?)
         OR (?<>'' AND p.phone=?)
         OR (?<>'' AND replace(lower(p.canonical_name),' ','')=?)""",
      (email,email,ph,ph,name,name)).fetchall()
    con.close()
    return jsonify({"duplicate":bool(rows),"matches":[dict(r) for r in rows]})

@app.get("/health")
def health(): return {"ok":True}
if __name__=="__main__": app.run(host="0.0.0.0",port=8000)
