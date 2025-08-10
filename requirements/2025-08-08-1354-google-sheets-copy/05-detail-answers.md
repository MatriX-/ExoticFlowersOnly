# Detail Answers

**Date:** 2025-08-08 13:58

## Q6: Should the tool check for updates automatically on a schedule or only when manually triggered?
**Answer:** Every 1 hour
**Implication:** Implement automated scheduling with 1-hour intervals using cron or scheduler

## Q7: Do you want the copied sheet to have a specific naming convention or just append "Copy" to the original name?
**Answer:** Name it "ExoticFlowersOnly Menu"
**Implication:** Use fixed name "ExoticFlowersOnly Menu" for the processed sheet

## Q8: Should the tool preserve the original sheet structure after removing columns A, F, G (i.e., shift remaining columns left)?
**Answer:** Yes, shift columns left, and only copy data before "FOR COA and MEDIA REFERENCE ONLY" row
**Implication:** Delete columns A, F, G with left shift; stop copying at row containing "FOR COA and MEDIA REFERENCE ONLY"

## Q9: Do you need the tool to handle authentication tokens automatically or are you okay with re-authenticating each time?
**Answer:** Auto
**Implication:** Store and refresh OAuth tokens automatically for seamless operation

## Q10: Should the tool create a new copy each time or update the existing copied sheet in place?
**Answer:** Update
**Implication:** Update existing "ExoticFlowersOnly Menu" sheet in place rather than creating new copies