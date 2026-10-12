# Month-end close agent: no-names walkthrough (source for /services/month-end-close/)

Sourced by Grok Bot on 2026-10-11 from lumic's private repos, on Christian's instruction. This file names no client, person or product. Keep it that way on the page.

## How it works, step by step
1. **Read the period.** The agent reads the month's activity straight from the ERP. Reading is all it does at this stage.
2. **Prepare the recurring entries.** It prepares the entries a controller builds by hand every month:
   - payroll journal entries, with month-end accruals and reversals when a pay period straddles the month
   - bank-reconciliation adjustments
   - inventory clearing
   - the monthly adjusting entries
3. **Tie out.** It runs the tie-outs before anything is approved: bank reconciliation, intercompany tie-out where a business runs more than one company, and an income-statement tie-out.
4. **Stage, don't post.** Every entry lands in the ERP **unposted**. Each one is balanced, checked against existing entries so nothing is entered twice, and reversible until a person posts it.
5. **Controller approves.** The controller reviews each entry and posts it. Posting stays a human action, every month.
6. **Live result.** A live income statement (consolidated, where there is more than one company) shows the result as soon as the entries post. A monthly management report reads the books live and is finalized by the controller after month-end.

## Proof
None on the page. Per Christian (2026-10-11, 9:33 PM CT): general process only, with no client information or client proof figures on any page.

Sources: lumic private repos (payroll agent spec and knowledge doc; payroll and month-end scripts).

## Do NOT publish
Client names, people's names, product names, dollar amounts, account numbers, or any new figure (close-days, hours saved). None is counted in the repos.
