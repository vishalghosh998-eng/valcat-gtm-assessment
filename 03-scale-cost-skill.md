The way I'd run this at 14,000 rows: first, the QA gate. That's the Python script and it's free. Whatever fails gets cut. Only the rows that pass go to enrichment, because enrichment is what costs money.

The point of running the script first is to qualify or disqualify leads at the earliest stage, before any money is spent. So from 14,000 rows, roughly 6,000 get rejected, and only the clean 8,000 go forward to ZoomInfo enrichment. That alone cuts the enrichment cost roughly in half compared to what the previous engineer was doing.

Before we buy anything — Dev wants 20,000 more contacts. Before that conversation happens, the segment table shows 8,457 verified rows where only 6,027 were contacted. That's 2,430 verified leads already paid for and never touched. On top of that, the master file has 14,203 records but the segment table only accounts for 9,100 — there's a mismatch of around 5,000 records. I don't know if those are verified but they exist. We can run the pipeline on those and reuse the 2,430 leads that are already verified. No reason to spend money on new data before we've worked through what we already have.

Two things that failed and I only caught by going through the output manually:

First — duplicate detection was case-sensitive. Dana Whitfield appeared twice, same person, but one email had capital letters. Script treated them as two different leads. Both passed.

Second — no rule for free email providers. Karen Ostrowski, COO at a real company, passed every check but had a personal Gmail. Script let her through. Personal inboxes don't belong in a B2B send.

Third — if you don't use a proper CSV parser and just split on commas, multiline fields break the row count. Everything downstream would be off. The reconciliation gate catches it, but only if you built it right.

What I would not trust this script to do unattended: Alan Frisk has an email at a different company domain than the one listed. Script flags it as a warning but doesn't block it. Someone needs to check that manually before sending.