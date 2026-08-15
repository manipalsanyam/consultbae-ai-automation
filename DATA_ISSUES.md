# Data Issues Report

The source data is intentionally imperfect. The following issues were identified and handled.

| Issue | Source | Handling |
|---|---|---|
| Exact duplicate Naukri records | Source 1 rows 24/30 (`Rohit Verma`) | Kept both source rows as evidence; merged to one person using the same email + phone. |
| Exact duplicate Naukri records | Source 1 rows 26/36 (`Nikhil Chopra`) | Kept both source rows; merged to one person using the same email + phone. |
| Blank record | Source 2 row 11 | Excluded because name/email/rate/location/status/skills are all blank. |
| Duplicate header embedded as data | Source 3 row 15 | Excluded because `Name / Phone Number / City / Verified / Projects Completed` is a header, not a person. |
| Duplicate/malformed row | Source 2 row 19 | The email and skill fields are shifted: the email column contains `react, javascript, mysql` and the worker name is Isha Chopra. It is treated as a duplicate of the valid Isha Chopra row rather than as a new identity. |
| Same name, conflicting identity | Source 3 `Arjun Mehta` appears with phone `9000000131` and again with `9000000272` | Do **not** merge by name alone. The `9000000131` record links to the Naukri/phone identity; the `9000000272` record remains a separate person. |
| Same name, multiple email identities | Source 2 `Deepak Nair` appears with two different emails | Do not merge the two source-2 identities solely by name. The identity that matches Naukri/source-3 phone is linked; the other is retained separately. |
| Case inconsistency in names | Sources 1–3 | Normalize for matching; retain original spelling in source records. |
| Case inconsistency in emails | Source 2 | Normalize emails to lowercase before matching. |
| Phone formatting inconsistency | Sources 1 and 3 | Strip `+91`, spaces and punctuation; use the last 10 digits as the normalized Indian phone key. |
| City aliases/case differences | All sources | Normalize `Gurgaon/Gurugram`, `Bangalore/Bengaluru`, `New Delhi/Delhi NCR` and case variants for matching. Original city is retained. |
| Verification values vary | Source 3 | `Y/yes/Yes` and `N/no/No` are semantically equivalent; source value is preserved in raw payload. |
| Status values vary by case | Source 2 | `ACTIVE/Active/active`, `Paused/paused`, `Inactive/inactive` are case variants. No semantic case distinction is assumed. |
| Rate uses mixed units | Source 2 | Values such as `1415/hr` and `15k/month` are not silently converted because a conversion policy is not supplied. Raw values are preserved. |
| CTC uses mixed units/scale | Source 1 | Many CTC values are large numeric amounts while some are small values such as `4.2`, `5.1`, `11.9`. These are retained rather than guessed as annual/lakh units. |
| Applied dates have many formats | Source 1 | The source parser retains raw dates. No locale-based rewriting is applied during identity resolution. |
| Future applied dates | Source 1 | Several dates are after 14-Aug-2026. They are flagged as suspicious, not silently changed. |
| Near-duplicate names | Sources 1–3 | Names such as Isha Chopra/Sneha Chopra are similar, but no automatic merge is made without a strong identifier or an unambiguous exact name+city match. |
| Cross-system IDs do not exist | All sources | Entity resolution uses normalized email/phone and conservative exact name+city logic. |
| Missing email in CBNexus | Source 3 | Phone + name/city are used where safe. No fake email is generated. |
| Missing phone in Gig Workers | Source 2 | Email is the strongest cross-system identifier; otherwise conservative name+city matching is used. |

## Matching policy

The matching order is deliberate:

1. **Exact normalized email**
2. **Exact normalized phone**
3. **Exact normalized name + normalized city only when unambiguous**
4. Otherwise, keep separate records.

I intentionally did not make fuzzy name similarity an automatic merge rule. A false positive is more damaging than leaving an ambiguous person separate, and the database keeps all raw source rows so an operator can review ambiguous cases later.

## Result

With the supplied files:
- 103 usable source rows are ingested.
- 55 master person records are produced.
- Source-level evidence is preserved in `source_records`.
