# Source review: Front Desk Residence Hall Manual transcription

**Source:** `data/procedures/residence_hall_front_desk_knowledge_base.md`. A structured transcription
of photographed manual pages 18 and 24–32. **Not independently verified as current.** There is no
public URL. Every answer that cites it shows: *"From a transcription of the Front Desk Residence Hall
Manual, not independently verified as current. Follow the instructions of your headstaff if they
differ."*

The Markdown text is never edited by the app. Flags live in
`residence_hall_front_desk_knowledge_base.meta.json` (review notes, related catalog links) or are
detected from the text itself (source limitations, web addresses). Each flag is shown to users as a
"Flagged for review" or "Incomplete source" notice when the section is cited.

## Needs manual verification against the photographs

| Section | Issue | How it's flagged |
|---|---|---|
| Excessive Lockouts — Access Cards | The manual note says "lost lockout charges" in the excessive-lockouts section, word for word the same as the Lost Card note. Possibly copied during transcription. | review note |
| Excessive Lockouts — Keys | 4 steps, while the Access Cards version has 5 (no "complete the back of the lockout card" step). A step may be missing. | review note |
| Giving Recored Keys to Residents | The manual note about *charging* for recores sits under this procedure, but charging happens in "Steps for Recore". Check where it belongs. | review note |
| Steps to Issue Access Card, Steps for Returned Cards, Steps for Lost Card | They contain `https://housing.utk.edu/information-technology/`. Automated checks get HTTP 403 (Cloudflare), so it has not been verified. It is replaced in model evidence and never shown as a link. Answers link the verified **Lockout Card Access** portal instead. | automatic (URL detected) |

**To add the Housing IT URL** once someone has opened it in a browser and confirmed it: add it to
`data/resources.json` as a verified `webpage`, then add its ID to the `related` lists in the
`.meta.json`. Nothing else changes.

## Incomplete in the source (shown to users)

| Section | Limitation (from the transcription) |
|---|---|
| Return to Sender (pp. 30–32) | "The photographed page ends after this substep; any additional return-to-sender instructions are not included." |
| School Dude — Problem Type Reference (p. 18) | "Steps 1–3 of this page-18 procedure were not supplied." Only steps 4–5 and the problem-type table are available. |

## Structural choices worth knowing

- Page ranges belong to `##` groups, so each procedure cites its whole group's range (e.g.
  "Checking IN Packages, pp. 30–32"). This is accurate but not page-precise.
- "Mail & Delivery Processing — Overview" is the group introduction (mail types, SC Logic). It's a
  separate unit so it can be cited.
- Manual page numbers (printed pages, e.g. pp. 30–32) are different from PDF citations (page
  positions in the file, e.g. page 5 of the job description PDF).

## Pages 16 and 39 (merged 2026-11-14)

Source: a second transcription of the same manual (photographs of pp. 16 and 39). It's merged into
the same Markdown file; see its preamble. Text is unchanged except that sub-headings inside a
procedure are bold lines, and "Source limitation" lines repeat that transcription's coverage notes.

| Section | Issue | How it's flagged |
|---|---|---|
| **Fire Panel Response (p. 39)** | Contains fire-panel **operating instructions** (acknowledge within 15 s; silence then reset after a confirmed nuisance alarm) from an unverified transcription. The source itself says it doesn't replace building-specific fire procedures, emergency training, or responders' directions. | **Safety-critical** (sidecar `safety`): emergency notice shown first; Larry gives escalation only; a code guard replaces any answer containing acknowledge/silence/reset. Confirm against current official building fire procedures. |
| SchoolDude Maintenance Requests (p. 16) | Only step 1 ("New Work Order") is visible; p. 18 has steps 4–5, so **steps 2–3 are missing** (probably p. 17). Spelled "SchoolDude" here and "School Dude" on p. 18. | Incomplete source + review flag (cross-reference) |
| Equipment Checkout / Check-In (p. 16) | **Check-in steps aren't specified;** checkout rules vary by hall. | Incomplete source |
| Resident Report / Area Coverage Follow-Up (p. 39) | **Starts mid-procedure;** the title and initial steps aren't supplied (likely on p. 38). | Incomplete source |
| Public Room Reservations (p. 16) | Names **25Live**, but there's no verified link; "OA" isn't defined. | Not linked (no catalog entry) |
