# Payroll agent: no-names walkthrough (source for /services/payroll/)

Sourced by Grok Bot on 2026-10-11 from lumic's private repos, on Christian's instruction. This file names no client, person, payroll provider or accounting product. Keep it that way on the page.

## How it works, step by step
1. **Intake.** The controller drops the reports the payroll provider sends after each run into one drop zone: the general-ledger summary, plus the payroll register when there is one. Each file is recognised by what it contains, not by its name.
2. **Build.** The agent builds the payroll journal entry from those reports, using posting rules **derived from the company's own posted history**, not typed in by hand. When a pay period reaches back into the previous month, it also builds the month-end **accrual** and its **reversal**.
3. **Checks.** Every entry has to balance to the penny, or it can't be saved. The entry total must tie to the provider's total. Per-person lines are proved against the register where it's available.
4. **New lines.** A line the agent has never seen stops the run. It is not guessed: the controller picks the account from a shortlist, and the agent remembers that choice for every later payroll.
5. **Review.** The controller sees a short review screen: the totals reconcile, debits equal credits, and which lines need a decision, each with the evidence. Then the agent runs a full check against the accounting system without posting anything.
6. **Post.** Writing to the books happens **only on the controller's click**, and only after a passing check on the current build. Every guard runs again inside the write: balanced, active accounts only, a duplicate check, a company-file check. It stops at the first failure.
7. **Record.** Each posted entry is logged with its transaction number, and the source files are fingerprinted. A posted payroll can't be rebuilt or posted twice.

## Proof
None on the page. Per Christian (2026-10-11, 9:33 PM CT): general process only, with no client information or client proof figures on any page.

Sources: lumic private repos (payroll agent spec and knowledge doc; payroll and month-end scripts).

## Do NOT publish
Client names, people's names, the payroll provider's name, any accounting product name, dollar amounts, period counts, account numbers. The page claims only what's above.
