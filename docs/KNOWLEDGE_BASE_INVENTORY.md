# ResLink AI — Knowledge Base Inventory

**Purpose:** the main reference for what ResLink AI (and Larry) currently knows, and what's missing.
**Audited:** 2026-11-14 at commit `6316cb6`, from the repository only (no outside information).
**Updated:** 2026-11-14. Added the **eRezLife** portal (team-supplied URL and uses; sign-in page
verified as reachable; contents not inspected).
**Sources inspected:**
- `data/resources.json` (catalog)
- `data/procedures/residence_hall_front_desk_knowledge_base.md` and `.meta.json` (procedures + sidecar)
- `data/documents/*.pdf` (text extracted read-only)
- `docs/SOURCE_REVIEW.md`, `docs/DECISIONS.md`, `docs/EVALUATION.md`

**Excluded on purpose:** `data/bulletins.json`. The Staff Bulletin is **fictional demo data** and is
not part of Larry's knowledge base (it's never indexed or sent to Gemini).

**How to read the link statuses:**

| Status | Meaning |
|---|---|
| **Verified (reachable)** | Supplied by the team, and an HTTP check on 2026-11-13 reached the expected sign-in page or PDF. This does **not** mean the content behind a sign-in was inspected, or that a document is current. |
| **Unverified** | Appears in a source, but hasn't been confirmed. |
| **Missing** | No URL exists in the repository. |

**Resource kinds used below:**

| Kind | Meaning |
|---|---|
| **Login portal** | An online system that needs a sign-in. |
| **Verified online form** | A form you fill in online. Maxient is reached through a sign-in, so it counts as both a form and a portal. |
| **Reference document** | A PDF or transcription you read. |
| **Paper form** | A physical form, log, binder or stamp at the desk. **No online version exists in ResLink.** |

Use the checkboxes in Section 4 to track progress as information is collected.

---

## 1. Existing Resource Links

The catalog is `data/resources.json`: **8 resources in 6 dashboard categories.** Larry may only link
to these.

### Maintenance

| Resource | Category | Description and purpose | URL | Sign-in | Type | RA uses it to… | URL status | Limitations / flags |
|---|---|---|---|---|---|---|---|---|
| Maintenance Request Portal (UTK Housing, Asset Essentials) | Maintenance | UTK Housing's maintenance request portal on Asset Essentials (Brightly Software). | https://assetessentials.dudesolutions.com/UTKHousing | **Yes.** It redirects to a Brightly/Siemens sign-in page. | Login portal | Submit maintenance work orders (the RA Job Description, p. 4: "Submit SchoolDude work orders"). The manual's lockout charges (lost card, excessive lockouts, recores) are also filed as "School Dude" work orders. | Verified (reachable) | Content behind the sign-in wasn't inspected. **That this portal *is* "School Dude" is an inference** (DECISIONS 17): the domain is dudesolutions.com, the SchoolDude name appears in the sources, and the team linked the two. Confirm it. How to *start* a request (p. 18 steps 1–3) is missing. |

### Reporting

| Resource | Category | Description and purpose | URL | Sign-in | Type | RA uses it to… | URL status | Limitations / flags |
|---|---|---|---|---|---|---|---|---|
| Incident Report Form (Maxient) | Reporting | UT incident reporting form in Maxient. | https://cm.maxient.com/reportingform.php?UnivofTennessee&layout_id=2 | **Yes.** It redirects to UT Central Authentication Service (NetID). | **Online form behind a login portal** | Document policy violations and incidents. The RA Job Description says documentation "must be submitted immediately following the incident in Maxient" (p. 4). | Verified (reachable) | Form fields and contents weren't inspected (behind sign-in). **No procedure** explains what to put in a report. |

### Programming

**No resources in this dashboard category.** Program proposals and programming documentation are
submitted through **eRezLife**, which is listed under RA Portals. There are still no programming
procedures.

### Policies

| Resource | Category | Description and purpose | URL | Sign-in | Type | RA uses it to… | URL status | Limitations / flags |
|---|---|---|---|---|---|---|---|---|
| Resident Assistant Job Description (Residence Life Manual) | Policies | Official RA position description (printed manual pp. 44–49): responsibilities, expectations, confidentiality, on-hall duty, paperwork, terms of employment, academic standards, pay. | https://studentlife.utk.edu/housing/wp-content/uploads/sites/9/2024/05/Resident-Assistant-Job-Description-1.pdf | No | Reference document (PDF, 6 pages) | Look up RA duties and rules: desk hours, open-door hours, GPA, the 5 P's, confidentiality, paperwork. | Verified (reachable) | Upload path is `2024/05`; **whether it's the current version is unknown.** Citations use PDF pages 1–6, which differ from the printed manual pages 44–49. |
| University Housing Policies | Policies | Residence hall policies (filename dated **7.21.2023**). | https://studentlife.utk.edu/housing/wp-content/uploads/sites/9/2024/05/UH-Policies-7.21.2023.pdf | No | Reference document (PDF, 8 pages) | Answer resident policy questions (quiet hours, guests, alcohol, appliances, keys and lockout keys, etc.). | Verified (reachable) | **Dated 2023; whether it's current is unknown.** Refers to Hilltopics, the Standards of Conduct and the OIT home page, none of which are in the catalog. |

### RA Portals

| Resource | Category | Description and purpose | URL | Sign-in | Type | RA uses it to… | URL status | Limitations / flags |
|---|---|---|---|---|---|---|---|---|
| Lockout Card Access (Housing RA Login) | RA Portals | Housing RA login page for lockout card access. | https://saweb.asa.utk.edu/housing_ra/ra_login.asp | **Yes** (NetID and password; a bare "Housing Login" form) | Login portal | Assign or return temporary Access Card permissions during lockouts. | Verified (reachable) | **This is not the paper lockout card form** (that form is kept at the front desk). The manual reaches card access through a *different, unverified* URL (Section 5); the team assigned this portal to the lockout procedures. Content behind the login wasn't inspected. |
| Roster Information (StarRez) | RA Portals | UTK StarRez housing portal for roster information. | https://utk.starrezhousing.com/StarRezWeb/dashboard/1596 | **Yes** ("UTK - Staff SSO Login") | Login portal | Look up rosters and room assignments; the mail procedures also search StarRez for room numbers and forwarding addresses. | Verified (reachable) | The URL is a specific dashboard (`/dashboard/1596`). **Whether it's the right entry point for the mail lookups is unverified.** Roster data is confidential (Job Description p. 3). |
| eRezLife — RA Reporting & Programming | RA Portals | The portal RAs use to complete and submit administrative reports, programming documentation, and resident engagement records. | https://utk.erezlife.com/ | **Yes.** It redirects through UT Shibboleth to UT Central Authentication Service (NetID). | Login portal (university housing management portal) | Submit **weekly reports**, **daily logs**, **program proposals**, **Vol Chats**, and **suite visits**. | Verified (reachable), checked 2026-11-14 | **The five uses are team-supplied;** the portal's contents behind the sign-in weren't inspected. **No in-portal procedures** are documented, so Larry names eRezLife but doesn't explain how to fill anything in. |

### Procedures

| Resource | Category | Description and purpose | URL | Sign-in | Type | RA uses it to… | URL status | Limitations / flags |
|---|---|---|---|---|---|---|---|---|
| Front Desk Residence Hall Manual | Procedures | Front desk procedures: lockout cards, keys, recores, packages and mail, School Dude problem types. **Structured transcription of photographed manual pages 18 and 24–32.** | — (none) | n/a | Reference document (local Markdown transcription) | Follow front desk procedures step by step. | **Missing (by design):** no public URL exists; ResLink never shows a link for it. | **Not independently verified as current.** 2 incomplete units, 3 review flags, 3 procedures that mention an unverified URL. See Section 2 and Section 5. |

### Referenced in sources but **not** in the catalog

These are named in the sources, but ResLink has no verified link for them.

| Referenced item | Where it's mentioned | Kind | URL in repository | Status |
|---|---|---|---|---|
| Housing IT page → "Card Access Resources" → "Lockout Cards" | Manual: Issue Access Card (step 5), Returned Cards (step 1), Lost Card (step 1) | Webpage / portal path | `https://housing.utk.edu/information-technology/` (text only) | **Unverified.** HTTP 403 (Cloudflare) to automated checks. Never linked. |
| SC Logic (Intra Desktop Client) | Manual: Mail overview and package procedures | Desktop software on the post office computer | — | **Missing.** Not a web resource. Hall-specific credentials, which must never be stored. |
| "School Dude" | Manual (lockouts, recores, p. 18); Job Description p. 4 ("SchoolDude") | Work-order system | — (assumed to be the Maintenance Request Portal) | **Inferred mapping; confirm it.** |
| StarRez (mail lookups) | Manual: Sorting Paper Mail, Forwarding Mail | Login portal | — (assumed to be the StarRez roster URL) | **Entry point unverified.** |
| Hilltopics (student handbook) | Housing Policies p. 6; Job Description p. 3 | Reference document | — | **Missing** |
| Student Code of Conduct / Standards of Conduct | Housing Policies p. 6; Job Description p. 3 | Reference document | — | **Missing** |
| University Housing Website | Job Description p. 3 | Webpage | — | **Missing** |
| "Expectations of University Housing Staff" | Job Description p. 3 | Reference document | — | **Missing** |
| OIT home page (technology guidelines) | Housing Policies p. 7 (Computer Use) | Webpage | — | **Missing** |
| Community Development Model (CDM) | Job Description pp. 2, 4 | Reference document | — | **Missing** |
| Office of Student Conduct and Community Standards | Housing Policies p. 8 (resident complaints) | Office / contact | — | **Missing** (no contact information) |

### Paper forms, logs and physical items referenced in procedures

There's **no online version** of any of these in ResLink. They're physical items at the desk.

| Item | Used in | Notes |
|---|---|---|
| Resident's **lockout card form** (access cards) | Issue Access Card (steps 1, 15), Returned Cards (steps 8–9), Lost Card (step 11), Excessive Lockouts — Access Cards (step 4) | Kept "in the appropriate place at the front desk". The *back* records charges. |
| **Lockout card** (keys) | Issuing a Lockout Key, Returned Lockout Key, Recore, Excessive Lockouts — Keys | Kept in a bin, basket or "appropriate container". |
| Temporary **Access Card** (PIK number 888_____) | Access-card procedures | Physical card, stored in the Access Card area. |
| **Key binder / Key Log Binder** | Recore (steps 7–8), Giving Recored Keys (steps 3–4) | Records work order details and resident signatures. |
| **Recore Basket** | Recore (step 10) | Where completed recore lockout cards go. |
| Package **log** ("appropriate log") | Checking IN (step 11), Checking OUT (step 9) | Which log isn't specified. |
| **Damage package log**; **returned/forwarded log**; **F/RTS Log** | Damage/RTS/Forward Log; Forwarding Mail (step 5) | May be the same log; not specified. |
| **Signature Pad** | Checking OUT (step 7) | Hardware at the post office. |
| **Forward** stamp, **RTS** stamp, white mailing label | Forwarding Mail, Return to Sender | Physical supplies. |
| Hall **roster** (paper or printed) | Sorting Paper Mail (steps 2–3) | Each resident is assigned a mailbox letter. |
| Search **authorization form** | Housing Policies p. 8 | Must list 4 items (see Section 2, PDF passages). |

### Resource Summary

| Measure | Count | Details |
|---|---|---|
| Total catalog resources | **8** | 1 maintenance, 1 reporting, 0 programming, 2 policies, 3 RA portals, 1 procedures |
| Resources with a URL | 7 | All 7 are **Verified (reachable)** (six checked 2026-11-13, eRezLife 2026-11-14) |
| Missing URL | 1 | Front Desk Residence Hall Manual (no public link, by design) |
| Unverified URLs referenced in sources | 1 | `housing.utk.edu/information-technology/` (not in the catalog) |
| Referenced but not cataloged (no URL) | 10 | See the table above |
| Require a sign-in | **5** | Maintenance Portal, Maxient Incident Form, Lockout Card Access, StarRez, eRezLife |
| Need review | **3** | Front Desk Manual (flags, incomplete units, currency); both PDFs (currency: 2023 file, 2024 upload) |
| Inferred mappings to confirm | 2 | School Dude → Maintenance Portal; StarRez mail lookups → roster URL |

---

## 2. Existing Procedures

The knowledge base is `data/procedures/residence_hall_front_desk_knowledge_base.md`: **18 units in 4
sections** (16 procedures, 1 overview, 1 reference table). Each unit is retrieved whole.

**Page numbers** are the printed manual pages. A procedure inherits its `##` group's range, so
citations aren't page-precise. **Every** unit carries the note "not independently verified as
current".

Steps are copied **verbatim** from the transcription, including bold text, sub-bullets, manual
notes, template placeholders and source limitations. Nothing has been corrected. Template
placeholders such as "resident's name (UT ID # and room #)" are placeholders and must never be filled
in with real data.

### Lockout Card Procedures (pp. 24–26)

#### Steps to Issue Access Card

| Field | Details |
|---|---|
| Purpose | Issue a temporary Access Card to a locked-out resident and transfer their room access to that card. |
| When an RA uses it | A resident is locked out and needs temporary card access (the procedure sets 72 hours if the resident lost or broke their phone, 2 hours if the phone is in the room). |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual pp. 24–26 (inherited from group "Lockout Card Procedures"); evidence ID `front-desk-manual#steps-to-issue-access-card` |
| Related forms / portals / links | Lockout Card Access portal (catalog `lockout-card-access`, sign-in) — *mapping assigned by the team in the sidecar; the manual itself names a different, unverified URL (see step 5)*<br>**Paper:** the resident's lockout card form (kept at the front desk)<br>**Physical:** temporary Access Card (PIK number 888_____) |
| Completeness | Complete in transcription |
| Warnings / flags | **Not independently verified as current** (whole transcription).<br>**Unverified web address** in the steps (not linked by ResLink). |
| Missing information | Step 5 URL (`https://housing.utk.edu/information-technology/`) is unverified.<br>Where "the appropriate place" for lockout card forms is (likely hall-specific; not documented).<br>What to do if the resident cannot verify identity (not documented). |

**Documented steps (verbatim from the transcription; not edited):**

1. Find the resident’s lockout card form in the appropriate place at the front desk.
   - Verify who the resident is by asking for their NetID, birthday, and phone number.
2. Locate an Access Card that will be assigned to the student.
3. Begin filling out the lockout number, temporary card number (in **RED**), number of hours checked out (up to **72 hours**), and your initials.
4. Have the resident sign for the Access Card.
5. Go to https://housing.utk.edu/information-technology/.
6. Click **Card Access Resources**. Click **Lockout Cards**.
7. Log in with your NetID and password.
   - The NetID field is case sensitive; use all lowercase letters.
8. Click **Assign Room Permission to card**.
9. Enter the resident’s NetID.
   - The NetID field is case sensitive; use all lowercase letters.
10. Adjust duration considering circumstances (i.e., if resident lost or broke their phone = **72 hours**; if resident left phone in their room = **2 hours**; use your discretion or contact your headstaff for assistance).
11. Note why you are issuing the card.
12. Click **Submit**.
13. Find the PIK number (the **888_____**) on the bottom left of the card and click on the same number on the website.
14. Click **Submit**. Access has now been transferred to the resident on the Access Card.
15. Place the resident’s lockout card form in the appropriate place at the front desk for safekeeping while the card is checked out.
16. Explain to the resident that they must return the card to restore access to their VolCard and lost cards are **$25**.

#### Steps for Returned Cards

| Field | Details |
|---|---|
| Purpose | Return a temporary Access Card: restore access to the resident's VolCard and record the return. |
| When an RA uses it | A resident brings back a temporary Access Card. |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual pp. 24–26 (inherited from group "Lockout Card Procedures"); evidence ID `front-desk-manual#steps-for-returned-cards` |
| Related forms / portals / links | Lockout Card Access portal (catalog `lockout-card-access`, sign-in) — *mapping assigned by the team in the sidecar; the manual itself names a different, unverified URL (see step 5)*<br>**Paper:** the student's lockout card form (initial and date)<br>**Physical:** Access Card storage area |
| Completeness | Complete in transcription |
| Warnings / flags | **Not independently verified as current** (whole transcription).<br>**Unverified web address** in the steps (not linked by ResLink). |
| Missing information | Step 1 URL is unverified (same Housing IT address). |

**Documented steps (verbatim from the transcription; not edited):**

1. Go to https://housing.utk.edu/information-technology/.
2. Click **Card Access Resources**. Click **Lockout Cards**.
3. Log in with your NetID and password.
   - The NetID field is case sensitive; use all lowercase letters.
4. Click **Return Assigned Room Card**.
5. Type in the resident NetID or the Card PIK number (the **888_____**) on the bottom left of the card.
   - The NetID field is case sensitive; use all lowercase letters.
6. Click **Submit**. The access has now been transferred to the student’s VolCard.
7. Return the card to the correct area where Access Cards are stored.
8. Find the student’s lockout card form, and **initial and date** to indicate the card was turned in.
9. Place the lockout card form back in the appropriate place.

#### Steps for Lost Card

| Field | Details |
|---|---|
| Purpose | Mark a temporary Access Card as lost, move access back to the VolCard, charge the $25 lost-card fee through a School Dude work order, and notify headstaff. |
| When an RA uses it | A resident lost a temporary Access Card. |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual pp. 24–26 (inherited from group "Lockout Card Procedures"); evidence ID `front-desk-manual#steps-for-lost-card` |
| Related forms / portals / links | Lockout Card Access portal (catalog `lockout-card-access`, sign-in) — *mapping assigned by the team in the sidecar; the manual itself names a different, unverified URL (see step 5)*<br>Maintenance Request Portal (catalog `maintenance-request-portal`) — *assumed to be "School Dude"; see Section 5*<br>**Paper:** back of the lockout card (bill charge, date, work order number, initials)<br>**Email:** headstaff (address not documented) |
| Completeness | Complete in transcription |
| Warnings / flags | **Not independently verified as current** (whole transcription).<br>**Unverified web address** in the steps (not linked by ResLink). |
| Missing information | Step 1 URL is unverified.<br>The top of the School Dude request ("Fill out the top normally") is not documented anywhere; the p. 18 procedure is missing steps 1–3.<br>Headstaff contact address is not documented; the manual note says some headstaff handle charges themselves. |

**Documented steps (verbatim from the transcription; not edited):**

1. Go to https://housing.utk.edu/information-technology/.
2. Click **Card Access Resources**. Click **Lockout Cards**.
3. Log in with your NetID and password.
   - The NetID field is case sensitive; use all lowercase letters.
4. Click **Lost temporary access card**.
5. Type in the resident NetID or the Card PIK number.
   - The NetID field is case sensitive; use all lowercase letters.
6. Click **Submit**.
7. The card will now be marked lost and the student’s access will be transferred to their VolCard.
8. For a lost access card, the fee is **$25**. Notify the resident that they will be charged $25 for the lost access card to their student account.
9. Fill out a School Dude work order in addition to the back of the lockout card. Go to School Dude and go to **New Request**. Fill out the top normally. Select **“operational services”** as the craft. The important difference is in the request box.
10. In the description, write: **“Please charge resident’s name (UT ID # and room #) $25 for a lost access card charge”**.
11. To complete the back of the lockout card, input the bill charge (lost access card), the date, the work order number, and your initials indicating who filed this charge.
12. Email headstaff indicating the student information, the work order number, and the date you assigned the charge.

**Manual note:** Some building headstaff members may ask you not to process lost lockout charges yourself, but instead email them the lost card information and student information. Follow the instructions directed by your respective headstaff.

#### Excessive Lockouts — Access Cards

| Field | Details |
|---|---|
| Purpose | Charge the $25 excessive-lockout fee (5th and later lockouts) through a School Dude work order and notify headstaff. |
| When an RA uses it | A resident who already used 4 free lockouts needs another lockout. |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual pp. 24–26 (inherited from group "Lockout Card Procedures"); evidence ID `front-desk-manual#excessive-lockouts-access-cards` |
| Related forms / portals / links | Lockout Card Access portal (catalog `lockout-card-access`, sign-in) — *mapping assigned by the team in the sidecar; the manual itself names a different, unverified URL (see step 5)*<br>Maintenance Request Portal (catalog `maintenance-request-portal`) — *assumed to be "School Dude"; see Section 5*<br>**Paper:** back of the lockout card |
| Completeness | Complete in transcription — **flagged for review** |
| Warnings / flags | **Not independently verified as current** (whole transcription).<br>**Review flag:** The manual note here mentions 'lost lockout charges' although this section covers excessive lockouts; it matches the Lost Card note word for word and may be a transcription copy. Verify against the photographed page. |
| Missing information | How staff look up a resident's lockout count (the issue procedure records a "lockout number" on the form, but no lookup is described).<br>Top-of-request School Dude fields (p. 18 steps 1–3 missing). |

**Documented steps (verbatim from the transcription; not edited):**

1. For an excessive lockout (residents get **4 free lockouts**; their **5th and any after that** are considered excessive lockouts), the fee is **$25**. Complete lockout as normal but notify the resident that they have reached the limit of free lockouts and will be charged $25 for excessive lockouts.
2. Fill out a School Dude Work Order in addition to the lockout card. Go to School Dude and go to **New Request**. Fill out the top normally. Select **“operational services”** as the craft. The important difference is in the request box.
3. In the description, write: **“Please charge resident’s name (UT ID # and room #) $25 for an excessive lockout charge”**.
4. To complete the back of the lockout card, input the bill charge (excessive lockout), the date, the Work Order number, and your initials indicating who filed this charge.
5. Email headstaff indicating the student information, the Work Order number, and the date you assigned the charge.

**Manual note:** Some building headstaff members may ask you not to process lost lockout charges yourself, but instead email them the lost card information and student information. Follow the instructions directed by your respective headstaff.

### Key Procedures (pp. 27–29)

#### Issuing a Lockout Key

| Field | Details |
|---|---|
| Purpose | Lend a lockout key to a locked-out resident and record it on the lockout card. |
| When an RA uses it | A resident is locked out and is issued a physical lockout key (key-based halls/rooms). |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual pp. 27–29 (inherited from group "Key Procedures"); evidence ID `front-desk-manual#issuing-a-lockout-key` |
| Related forms / portals / links | **Paper:** lockout card (kept in a bin/basket)<br>**Physical:** lockout key<br>No online resource |
| Completeness | Complete in transcription |
| Warnings / flags | **Not independently verified as current** (whole transcription). |
| Missing information | Identity check differs from the Housing Policies PDF (photo ID); see Section 5.<br>Which halls use keys vs access cards is not documented. |

**Documented steps (verbatim from the transcription; not edited):**

1. Verify who the resident is by asking for their NetID, birthday, or phone number or checking their VolCard.
2. Fill out the lockout card by entering what number lockout it is.
   - **N** for No (resident has not lost the key).
   - What date **AND time** the key was checked out.
   - Date and time the key must be returned by (**within 24 hours**).
   - Initial.
   - Have the resident sign their name and explain the policy to them.
3. Give the resident the lockout key.
4. Place the lockout card in the bin/basket or appropriate container.

#### Returned Lockout Key

| Field | Details |
|---|---|
| Purpose | Record the return of a lockout key. |
| When an RA uses it | A resident returns a lockout key. |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual pp. 27–29 (inherited from group "Key Procedures"); evidence ID `front-desk-manual#returned-lockout-key` |
| Related forms / portals / links | **Paper:** lockout card<br>**Physical:** key box |
| Completeness | Complete in transcription |
| Warnings / flags | **Not independently verified as current** (whole transcription). |
| Missing information | What to do if the key is returned after 24 hours is covered only indirectly (recore procedure / Housing Policies p. 5). |

**Documented steps (verbatim from the transcription; not edited):**

1. When a resident comes to the desk to return a lockout key, get the lockout card and take their key.
2. Write the date and time they turned the key back in to you, and write your initials.
3. Put the key back in the box and put the card back into its original container.

#### Steps for Recore — Lost Keys or Lockout Keys Never Returned

| Field | Details |
|---|---|
| Purpose | Process a recore when a key is lost, broken/damaged, or a lockout key was never returned: lockout card entry, School Dude work order with the $45 charge template, Key binder entry, Recore Basket. |
| When an RA uses it | A resident lost their key or did not return a lockout key. |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual pp. 27–29 (inherited from group "Key Procedures"); evidence ID `front-desk-manual#steps-for-recore-lost-keys-or-lockout-keys-never-returned` |
| Related forms / portals / links | Maintenance Request Portal (catalog `maintenance-request-portal`) — *assumed to be "School Dude"; see Section 5*<br>**Paper:** lockout card (back of card), Key binder, Recore Basket |
| Completeness | Complete in transcription |
| Warnings / flags | **Not independently verified as current** (whole transcription). |
| Missing information | "Follow the beginning steps like a lockout" refers to another procedure (Issuing a Lockout Key) without saying which steps.<br>Top-of-request School Dude fields (p. 18 steps 1–3 missing). |

**Documented steps (verbatim from the transcription; not edited):**

1. If a resident has lost their key, follow the beginning steps like a lockout.
2. Fill out the lockout card by entering **R** in the lockout #.
   - If the key is lost, enter **Y** for Yes. If the key is broken or damaged, enter **N** for No.
   - What date **AND time** the key was reported lost.
   - In the box of returned date, write **RECORE**.
   - Initial.
   - Have the resident sign their name and explain the policy to them.
3. After this step the resident is good, but you will need to fill out a School Dude next.
4. In the description, write: **“Please recore room ___. Please cut (how many keys needed) new keys and the key breakdown (ex: 2A and 2B). Charge ‘Student Name,’ UT ID #, $45” — Staff initials, date**.
5. Mark Craft for **“Operational Services”**.
6. After School Dude is complete and you hit submit, **do not close out the tab yet**.
7. Find the Key binder.
8. Enter:
   - Date and time the Work Order was submitted.
   - The room #.
   - In problem, write **“Recore”**.
   - Your initials in the **“School Dude entered by”** box.
   - The Work Order # from the order you just submitted.
   - Write the same information out on four lines.
9. Fill out the same information on the back of the card.
10. Once this is complete place the lockout card in the **Recore Basket**.
11. Now you are done with a recore.

#### Giving Recored Keys to Residents

| Field | Details |
|---|---|
| Purpose | Hand new keys to a resident after a recore and record it in the Key Log Binder. |
| When an RA uses it | A resident comes to the desk to collect new keys after a recore. |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual pp. 27–29 (inherited from group "Key Procedures"); evidence ID `front-desk-manual#giving-recored-keys-to-residents` |
| Related forms / portals / links | **Paper:** Key Log Binder ("Resident" signature box)<br>**Physical:** newly labeled key tag |
| Completeness | Complete in transcription — **flagged for review** |
| Warnings / flags | **Not independently verified as current** (whole transcription).<br>**Review flag:** The manual note about charging for recores appears under this procedure, although charging happens in 'Steps for Recore'. Verify its placement against the photographed page. |
| Missing information | None identified beyond the general verification note. |

**Documented steps (verbatim from the transcription; not edited):**

1. The resident will come to the desk to get their new keys.
2. Verify who the resident is by asking for their NetID, birthday, or phone number or checking their VolCard.
3. Retrieve the Key Log Binder.
4. Have the resident sign in the box that says **“Resident”**.
5. Have resident return old key.
6. Place the newly labeled key tag on the key and give the key to the resident.

**Manual note:** Some building headstaff members may ask you to email them when charging for recores instead of following the steps above. Follow the instructions directed from headstaff over this manual.

#### Excessive Lockouts — Keys

| Field | Details |
|---|---|
| Purpose | Charge the $25 excessive-lockout fee for keys through a School Dude work order and notify headstaff. |
| When an RA uses it | A resident who already used 4 free key lockouts needs another lockout. |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual pp. 27–29 (inherited from group "Key Procedures"); evidence ID `front-desk-manual#excessive-lockouts-keys` |
| Related forms / portals / links | Maintenance Request Portal (catalog `maintenance-request-portal`) — *assumed to be "School Dude"; see Section 5*<br>**Paper:** lockout card |
| Completeness | Complete in transcription — **flagged for review** |
| Warnings / flags | **Not independently verified as current** (whole transcription).<br>**Review flag:** This version has 4 steps; the Access Cards version also includes a step to complete the back of the lockout card. Verify whether a step is missing from the transcription. |
| Missing information | Possibly missing step (complete the back of the lockout card), flagged for review.<br>Top-of-request School Dude fields (p. 18 steps 1–3 missing). |

**Documented steps (verbatim from the transcription; not edited):**

1. For an excessive lockout (residents get **4 free lockouts**; their **5th and any after that** are considered excessive lockouts), the fee is **$25**. Complete lockout as normal but notify the resident that they have reached the limit of free lockouts and will be charged $25 for excessive lockouts.
2. Fill out a School Dude Work Order in addition to the lockout card. Go to School Dude and go to **New Request**. Fill out the top normally. Select **“operational services”** as the craft. The important difference is in the request box.
3. In the description, write: **“Please charge resident’s name (UT ID # and room #) $25 for an excessive lockout charge”**.
4. Email headstaff indicating the student information, the Work Order number, and the date you assigned the charge.

**Manual note:** Some building headstaff members may ask you to email them when charging for excessive lockout charges. Follow the instructions directed from headstaff over this manual.

### Mail & Delivery Processing (pp. 30–32)

#### Mail & Delivery Processing — Overview

| Field | Details |
|---|---|
| Purpose | Background for mail work: post office setup, what SC Logic is, and the four types of mail a hall receives. |
| When an RA uses it | Orientation for desk/post office shifts; answering "what is SC Logic?" or mail-type questions. |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual pp. 30–32 (inherited from group "Mail & Delivery Processing"); evidence ID `front-desk-manual#mail-delivery-processing-overview` |
| Related forms / portals / links | **Software:** SC Logic (download during the first post office shift; no link or install steps) |
| Completeness | Complete in transcription |
| Warnings / flags | **Not independently verified as current** (whole transcription). |
| Missing information | Post office hours ("differ by hall"; not listed).<br>Handling procedures for overflow, large, and perishable packages are described as categories only. |

**Documented steps (verbatim from the transcription; not edited):**

All residence halls have partially functioning mail services in the lobby. Some halls have the post office attached to the front desk while other halls have a detached post office. Post office hours differ by hall.

**SC Logic (Intra Desktop Client)** is the package tracking/logging system used by mail services. It is available on the post office computer at each desk. Download the application during your first post office shift.

Mail items residence halls can expect to receive:

- **Paper Mail:** Typically delivered in bulk in the morning in either a mail bin or orange inter-campus mail folder.
- **Overflow Packages:** During peak package seasons, packages that do not make it into the package locker systems; delivered by mail service personnel.
- **Large Packages:** Packages that do not fit into the package locker system; typically delivered mid-afternoon by mail service personnel.
- **Perishable Packages:** Meal prep packages, cookie delivery, flower arrangements, etc.; delivered to the front desk by mail services personnel, flower companies, and edible arrangements.

#### Checking IN Packages

| Field | Details |
|---|---|
| Purpose | Log an arriving package in SC Logic, assign it to a resident (including RAW/unassigned packages), log it, and shelve it. |
| When an RA uses it | Packages arrive at the desk/post office. |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual pp. 30–32 (inherited from group "Mail & Delivery Processing"); evidence ID `front-desk-manual#checking-in-packages` |
| Related forms / portals / links | **Software:** SC Logic (Intra Desktop Client) on the post office computer — no link; hall-specific credentials (never stored in ResLink)<br>**Paper:** the "appropriate log" for packages |
| Completeness | Complete in transcription |
| Warnings / flags | **Not independently verified as current** (whole transcription). |
| Missing information | Which log is "the appropriate log" (name/format not documented).<br>How to obtain SC Logic hall credentials (not documented). |

**Documented steps (verbatim from the transcription; not edited):**

1. Log in to SC Logic. Usernames and passwords are hall specific.
2. Click **“Check In”**.
3. Assure status is set to **“Housing- Checked In”**.
4. Place cursor in blue barcode box.
5. Scan package (tracking number barcode).
   - If package is assigned to a student, name will appear highlighted in the database below. Skip to step 7.
   - If package is **NOT** assigned to student, this is considered a **RAW** package; proceed to step 6.
6. Find student in lower database using Name field.
   - Type in blank cell (**Last, First**).
   - Check building/room for correct student.
   - Highlight correct student by clicking row of data (should turn red).
7. Close pop-up alert box if applicable.
8. Update package type on right-hand side of screen (oversized, box, etc. from dropdown).
   - Use Note/Comment section if needed on right-hand side of screen.
   - Notes could include location of package, damaged box, etc.
9. Type your initials in the Note/Comments box.
   - You can right click key/lock button to maintain initials while signed in.
10. Click **submit** in bottom right of screen.
11. Log package on appropriate log. Include resident’s name, package ID number, date checked in, and your initials.
   - This is a very detailed-oriented process that requires you to be thorough. Take your time completing this step.
12. Circle tracking number barcode, write last name and room number on package, and place it on a designated shelf or bin.

#### Checking OUT Packages

| Field | Details |
|---|---|
| Purpose | Release packages to a resident in SC Logic with signature, and mark the log. |
| When an RA uses it | A resident picks up one or more packages. |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual pp. 30–32 (inherited from group "Mail & Delivery Processing"); evidence ID `front-desk-manual#checking-out-packages` |
| Related forms / portals / links | **Software:** SC Logic<br>**Physical:** Signature Pad<br>**Paper:** package log |
| Completeness | Complete in transcription |
| Warnings / flags | **Not independently verified as current** (whole transcription). |
| Missing information | None identified beyond the general verification note. |

**Documented steps (verbatim from the transcription; not edited):**

1. Log in to SC Logic.
2. Click **“Check Out”**.
3. Assure status is set to **“Housing- Picked UP”**.
4. Place cursor in blue barcode box.
5. Scan package(s) (tracking number barcode) being picked up by student. Tracking number barcode should be circled; ensure that you are using the correct barcode.
   - If a resident is picking up multiple packages, check them out simultaneously by scanning the barcode and clicking **“Enter”** between each package.
6. Check student’s VolCard.
7. Have student sign Signature Pad.
8. Click **“submit”** in bottom right of screen.
9. Indicate package was picked up in log.

#### How to Create/Check-In Package with No Barcode in SC Logic

| Field | Details |
|---|---|
| Purpose | Check in a package that has no barcode by generating a random "UH" ID in SC Logic. |
| When an RA uses it | A package arrives without a scannable barcode. |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual pp. 30–32 (inherited from group "Mail & Delivery Processing"); evidence ID `front-desk-manual#how-to-create-check-in-package-with-no-barcode-in-sc-logic` |
| Related forms / portals / links | **Software:** SC Logic |
| Completeness | Complete in transcription |
| Warnings / flags | **Not independently verified as current** (whole transcription). |
| Missing information | Whether generated-barcode packages also go on the package log (the check-in procedure logs packages; this one does not mention it). |

**Documented steps (verbatim from the transcription; not edited):**

All packages with a generated barcode will start with **“UH”**.

1. Log in to SC Logic.
2. Click **“Check In”**.
3. Assure status is set to **“Housing- Checked In”**.
4. Place cursor in a blue barcode box.
5. Right click and choose **“Generate Random ID”**.
6. Find student in lower database using Name field.
   - Type in blank cell (**Last, First**).
   - Check building/room for correct student.
   - Highlight correct student by clicking row of data (should turn red).
7. Close pop-up alert box.
8. Update package type on right-hand side of screen (oversized, box, etc. from dropdown).
   - Use Note/Comment section if needed on right-hand side of screen.
   - Notes could include location of package, damaged box, etc.
9. Click **submit** in bottom right of screen.

**Manual note:** To check out a package with a generated barcode, manually type the tracking number. Write down generated barcodes and attach to the package.

#### Damage/Return to Sender or Forward Log

| Field | Details |
|---|---|
| Purpose | Guidance for the damaged-package log and the returned/forwarded log, plus the rule that packages are not forwarded off campus. |
| When an RA uses it | A package arrives damaged, or an item is forwarded / returned to sender. |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual pp. 30–32 (inherited from group "Mail & Delivery Processing"); evidence ID `front-desk-manual#damage-return-to-sender-or-forward-log` |
| Related forms / portals / links | **Paper:** damage package log; returned/forwarded log |
| Completeness | Complete in transcription |
| Warnings / flags | **Not independently verified as current** (whole transcription). |
| Missing information | This section is guidance bullets, not numbered steps; what fields each log needs is not documented. |

**Documented steps (verbatim from the transcription; not edited):**

- The damage package log is only used for packages delivered in a state that may raise concern to a resident. Record the damaged package as soon as it is discovered so accountability is taken from front desk staff and placed onto the carrier who delivered the package.
- Keep the returned/forwarded log up to date when a package is forwarded or returned to sender. If staff forward an item, log the address it was forwarded to.
- **Do not forward packages to off-campus addresses; only paper mail should be forwarded.**

#### Sorting Paper Mail

| Field | Details |
|---|---|
| Purpose | Sort incoming letter mail into mailboxes using the roster, and decide what to recycle, forward, or return. |
| When an RA uses it | Daily paper mail delivery. |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual pp. 30–32 (inherited from group "Mail & Delivery Processing"); evidence ID `front-desk-manual#sorting-paper-mail` |
| Related forms / portals / links | Roster Information (StarRez) portal (catalog `starrez-roster`, sign-in) — *the catalog URL is a roster dashboard; whether it is the right StarRez entry point for mail lookups is unverified*<br>**Paper:** hall roster; mailboxes |
| Completeness | Complete in transcription |
| Warnings / flags | **Not independently verified as current** (whole transcription). |
| Missing information | None identified beyond the general verification note. |

**Documented steps (verbatim from the transcription; not edited):**

1. Gather all letter mail from USPS (in the box that they bring).
2. Look at the name (and room number if it is on there) on the mail and check the roster to make sure they live here.
3. The roster will have everyone’s name and room number that their mail should go in (each resident is assigned a specific letter). You can also find a resident’s room number by searching their names in StarRez.
4. If they live here, put their mail in their mailbox.
5. If they are not on the roster, check the postage (stamp).
6. If it says **Presorted Standard** or **Non-profit Organization**, you can recycle it.
7. If it is anything else, forward the letter or return it to sender.

#### Forwarding Mail

| Field | Details |
|---|---|
| Purpose | Forward paper mail to a resident's forwarding address from StarRez, then log and stamp it. |
| When an RA uses it | Mail arrives for someone with a forwarding address on file. |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual pp. 30–32 (inherited from group "Mail & Delivery Processing"); evidence ID `front-desk-manual#forwarding-mail` |
| Related forms / portals / links | Roster Information (StarRez) portal (catalog `starrez-roster`, sign-in) — *the catalog URL is a roster dashboard; whether it is the right StarRez entry point for mail lookups is unverified*<br>**Paper:** white mailing label, F/RTS Log, Forward stamp |
| Completeness | Complete in transcription |
| Warnings / flags | **Not independently verified as current** (whole transcription). |
| Missing information | None identified beyond the general verification note. |

**Documented steps (verbatim from the transcription; not edited):**

1. Log into StarRez.
2. Search for the student by last name. Choose the correct student.
3. Click **view addresses**.
   - Only forward if there is a forwarding address on file. If not, return to sender.
4. The address will typically be an off-campus address. Write address on white mailing label and place over residence hall address.
5. Log forwarded mail in the **F/RTS Log**.
6. Stamp letter with **Forward** stamp.

#### Return to Sender

| Field | Details |
|---|---|
| Purpose | Return paper mail for someone who doesn't live in the hall and has no forwarding address. |
| When an RA uses it | Mail cannot be delivered or forwarded. |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual pp. 30–32 (inherited from group "Mail & Delivery Processing"); evidence ID `front-desk-manual#return-to-sender` |
| Related forms / portals / links | **Paper:** RTS stamp |
| Completeness | **Incomplete** |
| Warnings / flags | **Not independently verified as current** (whole transcription).<br>**Incomplete source:** The photographed page ends after this substep; any additional return-to-sender instructions are not included. |
| Missing information | Any instructions after the NAA substep (the photographed page ends there). |

**Documented steps (verbatim from the transcription; not edited):**

1. After double checking that the student does **NOT** live here and that they don’t have a forwarding address, return it to sender.
2. Mark the address out for the building and the small barcode in the bottom right-hand corner of the envelope (so it will not be sent back to the building).
3. Stamp **RTS**.
   - Circle **NAA** if the student does not live in the residence hall (past or present).

**Source limitation:** The photographed page ends after this substep; any additional return-to-sender instructions are not included.

### School Dude — Problem Type Reference (p. 18)

#### School Dude — Problem Type Reference

| Field | Details |
|---|---|
| Purpose | Pick the right School Dude problem type for a maintenance request; final submission steps 4–5. |
| When an RA uses it | Submitting a maintenance work order. |
| Source | Front Desk Residence Hall Manual (transcription: `data/procedures/residence_hall_front_desk_knowledge_base.md`) |
| Pages / section | Manual p. 18 (inherited from group "School Dude — Problem Type Reference"); evidence ID `front-desk-manual#school-dude-problem-type-reference` |
| Related forms / portals / links | Maintenance Request Portal (catalog `maintenance-request-portal`) — *assumed to be "School Dude"; see Section 5* |
| Completeness | **Incomplete** |
| Warnings / flags | **Not independently verified as current** (whole transcription).<br>**Incomplete source:** Steps 1–3 of this page-18 procedure were not supplied. |
| Missing information | Steps 1–3 of the page-18 procedure (how to start a request).<br>Which problem type to use for lost-card/lockout charges is in the lockout procedures ("operational services" as the craft), not in this table. |

**Documented steps (verbatim from the transcription; not edited):**

| Problem Type | Description |
|---|---|
| Air Conditioning | Air conditioner issues. |
| Appliance Repair | Issues with stoves, refrigerators. |
| Close Circuit TV Systems | CCTV cameras and front desk monitors. |
| Custodial | Housekeeping / cleaning issues / trash cans / recycling bins / micro-fridge that is dirty. |
| Doors and Hardware | Door needs to be repaired or replaced. Door hardware is broken — latch, hinges, closures or a stuck key. Dead battery. |
| Electrical | Lighting or power outages. |
| Elevators | Issues with elevators. |
| Flooring | Issues with flooring, carpet, tile or baseboard. |
| Furniture | Issues with room furniture, signage, tackboards or common area. |
| General Maintenance | For maintenance issues that do not fit other problem types. |
| Grounds | **For Administrative Use Only** |
| Office Services | **For Administrative Use Only** |
| Operational Services | Lock recores, broken microfridges. |
| Painting | Wall repair needed. Command hooks. |
| Pest Control | Issues with bed bugs, insects or rodents. |
| Plumbing | Issues with sinks, toilets or water leak. |
| Shades/Blinds | Broken blinds or shades. |
| Washer/Dryer | Issues with washing machines or dryers. |
| Weight Equipment | Broken exercise equipment. |
| Windows | Broken glass in windows or doors. |

The visible continuation of the procedure on page 18 is:

4. Please select **NO** to indicate that you will **not** complete this work.
5. Press **Submit**.

**Source limitation:** Steps 1–3 of this page-18 procedure were not supplied.


### Procedural content inside the PDF sources

These passages aren't Markdown procedures, but Larry can retrieve them as evidence. The text below is
copied from the PDFs (whitespace normalized). **Page numbers are PDF pages.** For the Job Description,
printed page = PDF page + 43.

#### Lockout keys and lost keys (University Housing Policies, Keys and ID Cards, pp. 4–5)

> Possessing, using, or duplicating University keys, University access cards or University identification cards without authorization from the University or unauthorized entry into or use of University facilities is prohibited. Keys are to remain in the possession of the person to whom they are issued. Lost keys will result in a lock change and associated costs. A lockout key may be obtained at the residence hall front desk. For safety and security reasons, students are required to show a photo ID to receive a lockout key. The lockout key must be returned within 24 hours. If the key is not returned in the 24-hour period, the lock will be changed and the associated charges will be assessed to the student's account. Students are allowed to check out a lockout key four times per academic year without penalty. On the fifth and successive times thereafter, a service charge of $25 per lockout will be assessed to the student's account. Summer mini-term and summer sessions function as a combined separate time period.

*Cross-reference:* the manual's Key Procedures. The **photo ID** requirement differs from the manual (Section 5).

#### Abandoned Items (University Housing Policies, University Housing Procedures, p. 7)

> Residents are responsible for their own personal property at all times. When residents have not vacated assigned space as scheduled (internal transfers as well at the end of the contract period) and have not removed personal property, housing staff will make a reasonable attempt to contact the residents. Forty-eight (48) hours after this attempt to contact, the personal property will be removed and stored at the resident's expense. Residents will be billed a minimum labor charge of $50 plus $20/hour per employee involved in the removal and/or storage of abandoned personal property. Personal property removed by housing staff will be stored for 30 days. After 30 days, the items will be turned over to the Surplus Property office on campus. The Department of University Housing is not liable for damage to or loss of property that might occur during the course of removal or disposal. Residents will be billed for all costs incurred in removing personal property and restoration of the unit to usable space.

#### Inspection and Search Policy (University Housing Policies, pp. 7–8)

> (1) Entry by University authorities into occupied rooms … will be divided into three (3) categories: inspection, search, and emergency. … (a) Inspection: Scheduled inspections … shall be preceded, if possible, by twenty-four (24) hours' notice to the residents. University Housing conducts two fire drills each semester. An unannounced fire drill and an announced key in fire drill in accordance with state recommendations. During the inspection there will be no search of drawers, closets, or personal belongings. (b) Search: On-campus authorities will not enter a room for purposes of search without permission from the resident(s) or prior permission from the Vice Chancellor for Student Life, or a designee, unless in compliance with federal or state law. (c) Procedure for Search in Residence Hall Rooms: A request for permission to search may be made by the Hall Director, Assistant Hall Director, or their superiors when reasonable cause exists … If permission to search is verbally authorized, it must be verified in writing to the occupant(s) … A copy of the authorization form is presented to the occupant(s) or left in the room if the occupant(s) is absent. The authorization form shall contain the following: 1. Description of the place to be searched; 2. Name of the person authorizing the search; 3. Description of the item(s) sought; and 4. Name of the person requesting the search authorization. (d) Resident Complaint: … the resident may prepare a written statement for review by the Office of Student Conduct and Community Standards, or … state their complaint to an Assistant Director in University Housing or to a staff member of the Office of Student Conduct and Community Standards. …

(Ellipses are shortenings in this inventory only; the full text is in the PDF.)

#### Computer Use (University Housing Policies, p. 7)

> Students are expected to adhere to all University technology guidelines. Please refer to the OIT home page concerning technology use at the University

(The OIT home page has no link in ResLink.)

#### Peer Helper (RA Job Description, p. 3 / printed p. 46)

> 1. Establish effective communication with residents through active listening and responding with empathy and support. 2. Be familiar with and practice proper protocol procedures for emergency response situations. 3. Advise HD/ AHD of any resident concerns or conflict; ask for assistance and support. 4. Document incidents via an FYI email and/or an Incident Report. 5. Do not transport residential students to hospitals or provide them medical care. This does not apply to siblings/family members.

**Gap:** the "proper protocol procedures for emergency response situations" aren't in the knowledge base.

#### Enforcement of Policy and the 5 P's (RA Job Description, pp. 3–4 / printed pp. 46–47)

> 1. Educate residents and enforce all University rules, regulations, and policies. 2. Comply with the policies and procedures contained in the most current versions of the Resident Assistant Job Description, Hilltopics, Student Code of Conduct, University Housing Website and Expectations of University Housing Staff. Staff members who violate University and University Housing policies and procedures are subject to the same conduct process as other residents. In addition, staff members may be subject to job action, up to and including termination. 3. Contact the Hall Director or Area Coverage on duty to ensure appropriate action if the situation involves the "5 P's (Police, Paramedics/Personal Injury, Parents, Property Damage or Press). 4. Be responsible for thorough and accurate documentation of all violations of University Housing policies, regulations, and Standards of Conduct. Documentation must be submitted immediately following the incident in Maxient.

**Gap:** there are no contact details for the Hall Director or "Area Coverage on duty".

#### On-Hall Duty/Desk, Paperwork, Work Environment, Time Commitment (RA Job Description, pp. 4–5)

> **On-Hall Duty/Desk:** 1. Be in the building and accessible by phone or walkie-talkie at all times during your specified shift. 2. Complete all on-hall tasks, which include, but are not limited to; completing thorough hall walks and responding to conduct, emergency situations or resident concerns. 3. No non-University Housing employees behind the front desk.

> **Paperwork:** 1. Turn in all paperwork on-time by the specificized deadline(s). 2. Conduct health and safety inspections. 3. Distribute and collect surveys of the residential populations. 4. Assist in room check-in and check-out. 5. Post and remove approved flyers/signs on floors in a timely manner. 6. Update bulletin boards and complete door decs as outlined in the CDM. 7. Submit SchoolDude work orders and communicate facilities issues with supervisor in a timely manner.

> **Work Environment:** 1. Do not allow any non-staff members behind the front desk at any time. 2. Use of personal devices is limited to times when all jobs related tasks have been completed. 3. Anything being viewed or played behind the desk or in the Post Office must be appropriate for the public and set at a volume that does not disturb the business operation, which includes the function of the lobby. Use of headphones should be limited to one ear; necessary accommodations can be requested by contacting your supervisor. 4. Maintain an organized and clean front desk and/or Post Office while working. 5. Wear departmentally issued staff shirt to all shifts. No pajama pants. No clothing items representing another university/college/institution

> **Time Commitment (excerpt):** 3. Required to work an average of 6 hours per week at front desk and/or post office. 4. All overnight absences from your floor must be approved by the Hall Director.

**Responsibility 11 (p. 1)** lists "weekly reports, contact rosters, daily logs, fire drills" as RA
administrative tasks, but **no source says how or where to submit them.**

### Procedure Completeness Summary

| Section | Units | Complete in transcription | Incomplete | Review-flagged (content) | Unverified URL in steps |
|---|---|---|---|---|---|
| Lockout Card Procedures (pp. 24–26) | 4 | 4 | 0 | 1 (Excessive Lockouts — Access Cards) | 3 (Issue, Returned, Lost) |
| Key Procedures (pp. 27–29) | 5 | 5 | 0 | 2 (Giving Recored Keys; Excessive Lockouts — Keys) | 0 |
| Mail & Delivery Processing (pp. 30–32) | 8 | 7 | 1 (Return to Sender) | 0 | 0 |
| School Dude — Problem Type Reference (p. 18) | 1 | 0 | 1 (steps 1–3 missing) | 0 | 0 |
| **Total** | **18** | **16** | **2** | **3** | **3** |

There are **8 distinct units** with at least one incomplete marker, review flag or unverified URL.
All 18 are *not verified as current*.

---

## 3. Knowledge Base Coverage Matrix

Ratings reflect what the repository actually supports. **None of the areas is rated Complete.** Adding
eRezLife moved Programming from Missing to Partial (a portal exists, but no procedures).

| Area | Existing resources | Existing procedures / evidence | Coverage | Specific information still needed | Recommended next action |
|---|---|---|---|---|---|
| **Front desk operations** | Front Desk Manual; eRezLife (daily logs are submitted there) | Manual: packages, mail, lockouts, keys. Job Description: 6 h/week at the desk (p. 5); On-Hall Duty/Desk and Work Environment rules (p. 4) | **Partial** | Opening/closing a shift, what goes in a daily log (the portal is known, the content isn't), phone/radio handling, desk emergencies, guest sign-in (if any), post office hours per hall, SC Logic setup | Get the rest of the Front Desk Manual (pages beyond 18 and 24–32) and transcribe it in the same format |
| **Lockouts and access cards** | Lockout Card Access portal; Housing Policies pp. 4–5 | 9 manual procedures (4 card, 5 key); policy text on lockout keys | **Partial** (most substantial area) | Verify the Housing IT URL; resolve the photo-ID vs NetID/birthday/phone discrepancy; check the 3 review flags; how to look up a resident's lockout count; which halls use keys vs cards | Verify the URL in a browser; check the flags against the photos; ask headstaff about the ID requirement |
| **Packages and mail** | (none; SC Logic has no link); StarRez for lookups | 8 manual units (overview, check-in, check-out, no-barcode, logs, sorting, forwarding, RTS) | **Partial** | The rest of Return to Sender; handling of perishable, oversized and overflow packages; which log is "the appropriate log"; post office hours; SC Logic access | Get the page after Return to Sender; confirm the StarRez entry point for mail lookups |
| **Incident reporting** | Maxient Incident Report Form | Job Description: document incidents (FYI email and/or report); 5 P's escalation; submit in Maxient immediately (pp. 3–4) | **Partial** | What to include in a Maxient report; what an "FYI email" is and who receives it; on-call / Area Coverage contacts; emergency protocol | Add a public or approved incident-reporting guide; add an FYI-email procedure (non-sensitive template only) |
| **Maintenance** | Maintenance Request Portal (assumed = School Dude) | School Dude problem-type table + steps 4–5 (p. 18); "Submit SchoolDude work orders" (Job Description p. 4); charge templates in the lockout and recore procedures | **Partial** | **Steps 1–3** of submitting a work order; emergency vs routine maintenance contacts; confirm School Dude = Asset Essentials | Get manual p. 18 (and the page before it); confirm the system name with headstaff |
| **Housing policies** | Housing Policies PDF (2023); RA Job Description PDF | 30+ policy sections (Section 2 lists the PDF passages) | **Partial** | Whether the 2023 policies are current; Hilltopics and the Student Code of Conduct (referenced, not available) | Check for a newer policies PDF; add the Hilltopics / Code of Conduct links once verified |
| **Programming** | eRezLife (program proposals and programming documentation are submitted there; team-supplied) | — | **Partial** (was Missing before eRezLife) | How to plan and run a hall program; what a proposal must contain; deadlines; budget; the Community Development Model (CDM) | Collect the programming guide / CDM and the proposal requirements (PRD demo scenario 2) |
| **RA responsibilities and duty procedures** | RA Job Description PDF; StarRez (rosters); **eRezLife** (weekly reports, daily logs, Vol Chats, suite visits) | Responsibilities, expectations, confidentiality, meetings, on-hall duty, paperwork, terms (Job Description pp. 1–6) | **Partial** | **What a weekly report contains and when it's due** (where to submit it is now known: eRezLife); what Vol Chats and suite visits require; duty rounds procedure; emergency response protocol; health and safety inspection procedure; room check-in/check-out procedure | Collect the duty/on-call manual sections and the weekly report / Vol Chat / suite visit requirements |

---

## 4. Knowledge Base Expansion Checklist

**Where to add things:**
- **Links:** `data/resources.json` (verified URLs only).
- **Procedures:** a Markdown transcription in `data/procedures/` with `## Group (pp. X–Y)` / `### Procedure`, plus a sidecar `.meta.json` (`related`, `review`).
- **Problems:** `docs/SOURCE_REVIEW.md`.
- **After any change:** run `python -m scripts.build_index`, then add eval questions to `tests/eval_questions.json`.

### 4.1 Missing resource links

- [x] **High · Complete:** **Weekly report submission** link. Added **eRezLife** (`erezlife`, verified reachable 2026-11-14). Larry now names it for weekly reports, daily logs, program proposals, Vol Chats and suite visits (live check: 5/5). *How* to fill in a weekly report is tracked separately in 4.2.
- [ ] **High · Not Started:** **Housing IT "Card Access Resources → Lockout Cards"** page. *Needed:* browser confirmation of `https://housing.utk.edu/information-technology/` and the exact page. *Why:* used in 3 lockout procedures; currently hidden as unverified. *Add to:* `resources.json`, then the sidecar `related` lists.
- [ ] **Medium · Not Started:** **Hilltopics** and the **Student Code of Conduct**. *Why:* the sources defer to them for conduct rules. *Add to:* `resources.json` (policies).
- [ ] **Medium · Not Started:** **University Housing website** and **"Expectations of University Housing Staff"**. *Why:* named as governing documents (Job Description p. 3). *Add to:* `resources.json`.
- [ ] **Medium · In Progress:** **Programming resources.** Program proposals are submitted in eRezLife (added). Budget or request forms and programming guidelines are still missing. *Add to:* `resources.json` (programming).
- [ ] **Low · Not Started:** **OIT technology guidelines** page. *Why:* referenced by the Computer Use policy. *Add to:* `resources.json`.

### 4.2 Missing procedures

- [ ] **High · Not Started:** **Weekly report** procedure (what to include, deadline). *Where* is now known: eRezLife. *Add to:* new `data/procedures/*.md` section.
- [ ] **Medium · Not Started:** **Daily log, Vol Chat and suite visit** requirements (what each record needs and how often). The portal is known (eRezLife), but nothing about the content is documented. *Add to:* new `data/procedures/*.md` section.
- [ ] **High · Not Started:** **Hall program planning** procedure (PRD scenario 2), including the CDM. *Add to:* new procedures file.
- [ ] **High · Not Started:** **Emergency response / on-call protocol** ("proper protocol procedures", 5 P's escalation, Area Coverage contacts as roles only). *Add to:* new procedures file.
- [ ] **Medium · Not Started:** **Incident report (Maxient) how-to** and the **FYI email** process (non-sensitive template). *Add to:* procedures file + the Maxient catalog entry.
- [ ] **Medium · Not Started:** **Front desk shift open/close** and **daily logs**. *Add to:* the front desk manual transcription.
- [ ] **Medium · Not Started:** **Perishable / oversized / overflow package** handling. *Add to:* Mail & Delivery section.
- [ ] **Low · Not Started:** **Health and safety inspections** and **room check-in/check-out** procedures (listed RA duties). *Add to:* procedures file.
- [ ] **Low · Not Started:** **Post office hours** per hall. *Add to:* Mail overview (if public and current).

### 4.3 Incomplete procedures

- [ ] **High · Not Started:** **School Dude, steps 1–3** (manual p. 18). *Needed:* the photographed page(s) before steps 4–5. *Why:* every work-order and charge procedure depends on "fill out the top normally". *Add to:* School Dude section of the transcription.
- [ ] **Medium · Not Started:** **Return to Sender**: the steps after the NAA substep. *Needed:* the page after manual p. 32. *Add to:* the Return to Sender section.
- [ ] **Low · Not Started:** **Lockout count lookup**: how staff find a resident's number of lockouts. *Add to:* lockout sections.

### 4.4 Unverified information

- [ ] **High · Not Started:** Verify the **whole Front Desk Manual transcription is current** (photographed pages; source date unknown). *Add to:* `SOURCE_REVIEW.md`, then the catalog description once confirmed.
- [ ] **Medium · Not Started:** Confirm **School Dude = Maintenance Request Portal (Asset Essentials)**. *Add to:* the catalog entry's description and keywords.
- [ ] **Medium · Not Started:** Confirm the **StarRez entry point** for mail lookups (vs the roster dashboard URL). *Add to:* `resources.json` / sidecar.
- [ ] **Medium · Not Started:** Check whether the **Housing Policies (7.21.2023)** and the **RA Job Description (2024/05)** are the current versions. *Add to:* catalog descriptions.

### 4.5 Existing source discrepancies

- [ ] **High · Not Started:** **Lockout key identity check**: policies require a **photo ID**; the manual allows NetID, birthday or phone **or** VolCard. *Why:* this decides what an RA does at the desk. *Add to:* `SOURCE_REVIEW.md`; ask headstaff.
- [ ] **Medium · Not Started:** **Excessive Lockouts — Access Cards** note says "lost lockout charges" (possible copy). *Add to:* sidecar `review` (already flagged); resolve against the photo.
- [ ] **Medium · Not Started:** **Excessive Lockouts — Keys** has 4 steps vs 5 for access cards. *Add to:* sidecar (already flagged).
- [ ] **Low · Not Started:** **Giving Recored Keys** note placement. *Add to:* sidecar (already flagged).
- [ ] **Low · Not Started:** **Identity verification wording** differs inside the manual (Issue Access Card: "NetID, birthday, **and** phone number"; Issuing a Lockout Key / Giving Recored Keys: "NetID, birthday, **or** phone number or checking their VolCard"). *Add to:* `SOURCE_REVIEW.md`.

---

## 5. Source Verification Issues

| # | Issue | Affected content | Type | Current handling in ResLink |
|---|---|---|---|---|
| 1 | Front Desk Manual **not verified as current** | All 18 manual units | Currency | Compact note on every answer that cites it |
| 2 | **Housing IT URL** unverified (HTTP 403 to automated checks) | Issue Access Card s5; Returned Cards s1; Lost Card s1 | Unverified link | Replaced in evidence; a short note says it isn't linked; the team-assigned Lockout Card Access portal is shown instead |
| 3 | **"Lost lockout charges"** wording in the Excessive Lockouts — Access Cards note | Excessive Lockouts — Access Cards | Possible transcription error | Prominent "Possible transcription issue" warning |
| 4 | **Possible missing step** (back of lockout card) | Excessive Lockouts — Keys | Possible transcription error | Prominent warning |
| 5 | **Recore-charging note placement** | Giving Recored Keys to Residents | Possible transcription error | Prominent warning |
| 6 | **Return to Sender** cut off after the NAA substep | Return to Sender | Incomplete source | Prominent "Incomplete source" warning |
| 7 | **School Dude steps 1–3** not supplied | School Dude reference (p. 18) | Incomplete source | Prominent warning; Larry declines questions about steps 1–3 |
| 8 | **Photo ID (policy) vs NetID/birthday/phone or VolCard (manual)** for lockout keys | Issuing a Lockout Key vs Housing Policies p. 5 | **Cross-source discrepancy** | **Not flagged in the app yet.** Both sources can be retrieved. |
| 9 | "**and**" vs "**or**" in identity verification within the manual | Issue Access Card vs Issuing a Lockout Key / Giving Recored Keys | Internal inconsistency (may be intentional) | Not flagged |
| 10 | **School Dude ↔ Asset Essentials** mapping is inferred | Lockout charge and recore procedures; maintenance answers | Inferred mapping | Sidecar `related` links the Maintenance Request Portal |
| 11 | **StarRez** entry point for mail lookups | Sorting / Forwarding Mail | Inferred mapping | Sidecar `related` links the StarRez roster URL |
| 12 | **PDF currency:** Housing Policies dated 7.21.2023; both PDFs uploaded 2024/05 | All policy answers | Currency | Not flagged in answers |
| 13 | **Page precision:** procedures cite their group's page range | All manual citations | Citation granularity | Accepted (DECISIONS 31) |
| 14 | **PDF page vs printed page** (Job Description: printed = PDF + 43) | Job Description citations | Citation numbering | PDF page numbers are used for links |
| 15 | **eRezLife uses are team-supplied** (weekly reports, daily logs, program proposals, Vol Chats, suite visits); the portal's contents behind the sign-in weren't inspected | eRezLife answers | Unverified scope | Larry names the portal and the sign-in requirement only; no in-portal steps |

Amounts that appear in **only one source** (not conflicts, but worth confirming):
- $25 lost access card (manual)
- $25 excessive lockout (both sources)
- $45 recore charge (manual only; the policies say "lock change and associated costs")
- $50 + $20/hour abandoned-item handling (policies)

---

## 6. Inventory Statistics

| Measure | Value |
|---|---|
| Catalog resources | **8** (7 with a verified-reachable URL, 1 without a URL by design) |
| Resources requiring a sign-in | **5** |
| Unverified URLs referenced in sources | **1** |
| Items referenced in sources with no link in ResLink | **10** |
| Paper forms / logs / physical items referenced | **11** (Section 1 table) |
| Manual knowledge-base units | **18** (16 procedures, 1 overview, 1 reference table) |
| Incomplete units | **2** |
| Units with content review flags | **3** |
| Units that mention an unverified URL | **3** |
| Distinct units with any flag or incomplete marker | **8** |
| Procedural passages inside PDFs (listed in Section 2) | **7** groups |
| Coverage areas | **8**: 0 Complete, 8 Partial, 0 Missing (Programming moved to Partial with eRezLife) |
| Expansion checklist items | **27**: 1 Complete, 1 In Progress, 25 Not Started |
| Source verification issues | **15** |
| Fictional content excluded from the knowledge base | Staff Bulletin (`data/bulletins.json`, 8 demo announcements) |
