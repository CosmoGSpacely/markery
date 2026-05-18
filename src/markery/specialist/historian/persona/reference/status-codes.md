# Status Codes

## Field: `case_file.cfh_status_cd`

Numeric codes stored as integers in the database. The first digit indicates the broad category; the full code gives the specific disposition.

## Live Registrations (6xx)

| Code | Meaning |
|---|---|
| 600 | Registered |
| 609 | Registered — Section 15 acknowledgment |
| 610 | Registered — Section 8 accepted |
| 624 | Registered — renewed |
| 626 | Registered — backfile cancelled or expired (registration exists but physical file is gone or lapsed) |

**Historical note:** Codes 624 and 626 are the most common "live" codes in the 1900–1939 dataset. A 626 status means the registration was live as of the 2011 dataset snapshot, but the physical prosecution file is often marked "FILE DESTROYED." These are marks that survived on paper but lost their paper.

## Dead — Cancelled (7xx)

The registration existed and was subsequently cancelled or invalidated.

| Code | Meaning |
|---|---|
| 700 | Cancelled |
| 710 | Cancelled — Section 8 |
| 711 | Cancelled — Section 8 partial |

## Dead — Abandoned (8xx)

The application was never registered; it was abandoned during prosecution.

| Code | Meaning |
|---|---|
| 800 | Abandoned |
| 801 | Abandoned — failure to respond |
| 810 | Abandoned — express |

## Dead — Expired or Lapsed (9xx)

The registration existed but lapsed through non-renewal or non-use.

| Code | Meaning |
|---|---|
| 900 | Expired |
| 901 | Expired — Section 8 |

## Filtering in SQL

```sql
-- Live marks
WHERE CAST(cfh_status_cd AS VARCHAR) LIKE '6%'

-- Dead marks
WHERE CAST(cfh_status_cd AS VARCHAR) NOT LIKE '6%'

-- Live/dead as a label
CASE WHEN CAST(cfh_status_cd AS VARCHAR) LIKE '6%' THEN 'LIVE' ELSE 'DEAD' END AS status
```

## Historical Interpretation

For 1900–1939 filings, the overwhelming majority of marks are dead — expired, abandoned, or cancelled over the subsequent 70–100 years. A live mark (6xx) in this cohort is unusual and often represents a mark that was continuously renewed or republished, sometimes by a successor entity. The persistence of a mark across decades is itself a historical signal: the brand had sufficient commercial value to justify ongoing maintenance.

The distinction between abandoned (8xx) and expired (9xx) matters historically. An abandoned application suggests the company either couldn't clear the mark, ran out of resources, or stopped pursuing registration. An expired registration suggests the company existed long enough to register but eventually ceased, merged, or stopped renewing — a different point in the corporate lifecycle.
