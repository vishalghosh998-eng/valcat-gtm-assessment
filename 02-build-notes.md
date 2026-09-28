I got the vendor CSV. First thing I did was open it and look through it. There were some rows with no email address and a couple with names missing. So I decided to build a script using Claude that catches all of this automatically before anything goes into the sequencer.

What the script does — it reads the raw CSV, checks every row, and writes out a clean file. It also generates a QA report so I can see exactly what got excluded and why. If the numbers don't add up — output plus excluded has to equal total input — it refuses to write the file. Didn't want any rows silently disappearing.

First version gave me 18 rows out. I opened the CSV and went through it manually and found two problems.

First one — Dana Whitfield appeared twice. Same person, same LinkedIn, but one email was lowercase and the other had capital letters. Script treated them as two different people. Fixed by lowercasing before comparing.

Second one — Karen Ostrowski. Real COO at a real company, passed every other check, but her email was a personal Gmail. You can't send B2B outreach to someone's personal inbox. Added a rule to block Gmail, Yahoo, Hotmail and Outlook addresses.

Final output: 26 in, 16 out, 10 excluded. Reconciliation clean.