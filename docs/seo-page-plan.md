# get-lumic.com: multi-page SEO plan (draft)

Status: draft for review. Nothing here is built. Drafted 2026-10-11.

Today the site is one page (`public/index.html`). `scripts/build_markdown.py` makes `index.md`, `llms-full.txt` and `schema.jsonld` from it. This plan splits the site into pages that each match one search intent, using only the proof the site already shows.

## Rules every page follows

- Voice: third person ("lumic builds…"), lowercase "lumic". Never "we", "our" or "us". "You" and "your" for the reader are fine.
- No size reveals and no gap admissions (no "coming soon", "next on the list", "so far", team counts, "founder-led").
- No client or employer names. The private list in the playbook (`brand/site-banned-terms.txt`) is the source; this public repo must never repeat it. Clients stay anonymous, as today: "a specialty manufacturer", "a multi-company manufacturer and distributor".
- No prices, no quotes from real people, no invented numbers, clients or features.
- Honest integration depth: "the agent reads and prepares entries; a person approves before anything posts".
- "FDE" (Forward Deployed Engineer) is allowed, always with the plain words beside it.

### The main risk: product names on systems pages

**A systems page may say "lumic works with <product>" and describe what an agent does in that kind of system. It must never tie the product to a portfolio card, a client or a proof number.** No "64 of 67 bills", "about six weeks", "about 13 agent roles", "nine live dashboards", "specialty manufacturer" or "multi-company manufacturer and distributor" on any `/systems/` page, and no link from a systems page to a specific portfolio card. Links go to the services pages and the portfolio page as a whole. The reverse also holds: service, industry and portfolio pages never name a product. This is enforced in `qa.py` (see "QA changes").

## Keyword approach

get-lumic.com is a new, small domain. Head terms ("AP automation", "AI consultant") belong to large software vendors and directories, and a new domain will not rank for them for a long time. This plan targets:

- long-tail terms that describe the job and the method ("AI agent for accounts payable", "month-end journal entry automation");
- system plus job terms ("QuickBooks AP automation"), where the searcher already knows the system and the job;
- local terms ("AI automation St. Louis"), where competition is thin and the site already has strong local signals.

No keyword volumes were measured for this draft. Before each page is built, check the primary term in Google Keyword Planner or Search Console, and keep the term if the top results are service firms or small vendors, not only enterprise software.

## Page summary

| Page | Slug | Primary keyword | Intent | Priority |
|---|---|---|---|---|
| AP automation | /services/ap-automation/ | AI agent for accounts payable | Commercial | 1 (phase 1) |
| St. Louis | /st-louis/ | AI automation St. Louis | Local | 1 (phase 1) |
| How lumic works | /how-lumic-works/ | forward deployed engineers for small business | Informational | 1 (phase 1) |
| Home | / | lumic; Forward Deployed Engineers St. Louis | Navigational / commercial | Kept, trimmed in phase 1 |
| Services hub | /services/ | back-office automation services | Commercial | 2 |
| Month-end close | /services/month-end-close/ | month-end close automation | Commercial | 2 |
| Cash receipts and collections | /services/cash-receipts-and-collections/ | cash application automation | Commercial | 2 |
| Payroll | /services/payroll/ | payroll journal entry automation | Commercial | 2 |
| Dashboards and reporting | /services/dashboards-and-reporting/ | live ERP dashboards for small business | Commercial | 2 |
| Portfolio | /portfolio/ | AI agents in production examples | Commercial / informational | 2 |
| FAQ | /faq/ | what is a forward deployed engineer | Informational | 2 |
| Systems hub | /systems/ | accounting system automation | Commercial | 3 |
| QuickBooks | /systems/quickbooks/ | QuickBooks AP automation | Commercial | 3 |
| NetSuite | /systems/netsuite/ | NetSuite AP automation | Commercial | 3 |
| Sage 100 | /systems/sage-100/ | Sage 100 automation | Commercial | 3 |
| Manufacturing | /industries/manufacturing/ | AI automation for manufacturers | Commercial | 3 |
| Distribution | /industries/distribution/ | AI automation for distributors | Commercial | 3 |
| Sage Intacct | /systems/sage-intacct/ | Sage Intacct automation | Commercial | 4 |
| Service firms | /industries/service-firms/ | back-office automation for service firms | Commercial | 4 |

## Sitemap tree

```
/
├── services/
│   ├── ap-automation/
│   ├── cash-receipts-and-collections/
│   ├── payroll/
│   ├── month-end-close/
│   └── dashboards-and-reporting/
├── portfolio/
├── industries/          (short hub, phase 3)
│   ├── manufacturing/
│   ├── distribution/
│   └── service-firms/
├── systems/
│   ├── quickbooks/
│   ├── netsuite/
│   ├── sage-100/
│   └── sage-intacct/
├── st-louis/
├── how-lumic-works/     (/about/ 301s here)
├── faq/
└── privacy/
```

### Merges, splits and additions, and why

- **Cash receipts and collections: one page.** Same reader (whoever owns receivables), same data (live aging), and the site's proof links them: the receivables dashboard "feeds the collections agent". Two pages would be thin and would compete.
- **Purchasing and PO write-back: no own page.** It becomes a section on the AP page (PO matching is the AP agent's core step) and a line on the services hub. One proof line is not enough for a page.
- **Bank reconciliation: a section on the month-end page.** It is a close task, and the site gives it one line.
- **QuickBooks Online and Desktop: one page.** Searchers type "QuickBooks" first. The page has two sections, because the method differs (cloud app vs. desktop software on a dedicated computer).
- **Sage 100 and Sage Intacct: two pages.** Different products, different buyers (on-premises desktop ERP vs. cloud accounting), different searches. One "Sage" page would match neither well. Sage Intacct waits for phase 4, until it has enough distinct content (see the needs list).
- **Other systems.** Microsoft Dynamics 365 Business Central and Acumatica are the next candidates (mid-market ERPs with real "automation" searches). Xero, Bill.com, Ramp, Expensify, the payroll products, the CRMs, Shopify, FileMaker and the Microsoft and Google tools stay on the systems hub list only: low search demand for "<product> + AI agent" from lumic's buyer, or not enough distinct content.
- **About: named "How lumic works".** The method (FDE, on site, approval gates, security) is what buyers search for and what every other page links to. Leadership sits on this page. `/about/` 301s here.

## Page-by-page plan

Proof sources named below refer to sections of `public/index.html` (ids in brackets) and to `public/llms.txt`.

### Home `/`

- Keyword: brand name and "Forward Deployed Engineers St. Louis". Intent: navigational and commercial. Realistic: the brand term is already the domain's; the FDE + St. Louis pair has almost no competition.
- Purpose: in one screen, show what lumic does and get a booked call, or send the reader to the one page that matches their job.
- H1 (keep): "AI, deployed into your business and kept working."
- Title (keep): "lumic | Forward Deployed Engineers for business, St. Louis"
- Meta (new, shorter): "lumic's Forward Deployed Engineers put AI to work inside the systems your business runs, keep it working, and a person approves what matters. St. Louis."
- Keeps: hero and "Why lumic" film (#top), the demo and overview film with "Every figure is sample data" (#demo), "Watch each tool on its own" films (#films), the two offers (#services), the three lead portfolio cards (#proof), the systems list (`[data-systems-list]`, the only list outside `/systems/`), "How lumic works" three steps (#how), "Why lumic" (#why), contact (#contact).
- Moves off: the full portfolio grid ("Portfolio: what runs on lumic today" and "Eight more running in production") to `/portfolio/`; the full FAQ to `/faq/` (keep four questions, link the rest); leadership bios to `/how-lumic-works/#leadership` (keep the short "Finance first. Engineers second." line); "How the data flows" stays, or moves to `/how-lumic-works/` if the home page is still long.
- Adds: a row of links to the five service pages under #services, and a "See it in your system" link to `/systems/` beside the systems list.
- Links out: every service page, `/portfolio/`, `/systems/`, `/st-louis/`, `/how-lumic-works/`, `/faq/`. Links in: every page (logo and breadcrumb).
- Schema: Organization + ProfessionalService (existing, keep `@id` `#org`), WebSite, VideoObject for the two 16:9 films. FAQPage moves to `/faq/`.
- Needs: nothing.

### Services hub `/services/`

- Primary: "back-office automation services". Secondary: "AI agents for accounting", "managed AI agents", "finance automation services". Intent: commercial. Realistic: mid-tail; the page mostly ranks as the parent of the five service pages.
- Purpose: send the reader to the right job page, or to a call.
- H1: "AI agents for the back-office jobs your team does by hand."
- Title: "Back-office automation services | lumic"
- Meta: "lumic builds an AI agent for one back-office job at a time: AP, cash receipts, payroll, month-end and reporting. A person approves before anything posts."
- Content: the two offers, "Deploy an agent" and "Managed AI agents" (#services, both cards verbatim in substance); "Every deployment covers" list; the "Instead of → With lumic" table (#why); one card per service page; a purchasing and PO write-back line ("drafts purchase orders and writes them back to the ERP; approval-gated", from the portfolio grid).
- Links: out to the five service pages and `/portfolio/`; in from home, nav, every service page breadcrumb.
- Schema: Service (the managed-agent offer, provider `#org`), ItemList of the child services, BreadcrumbList.
- Needs: nothing.

### AP automation `/services/ap-automation/` (phase 1)

- Primary: "AI agent for accounts payable". Secondary: "vendor bill entry automation", "invoice to purchase order matching", "AP automation St. Louis". Intent: commercial. Realistic: "AI agent" + job phrasing is new and not yet owned by large vendors; the local variant has almost no competition.
- Purpose: an AP owner sees the agent do their job and books a call.
- H1: "An AI agent that enters your vendor bills. A person approves each one."
- Title: "AI agent for accounts payable: bill entry and PO matching | lumic"
- Meta: "lumic's AP agent reads each vendor bill from email, matches it to the PO and enters it once a person approves. Live about six weeks after the on-site day."
- Content:
  - The job, step by step: reads each bill from email, matches it to the PO, flags a price difference before anyone pays, enters it once approved (AP invoice agent card, #proof; demo text, #demo).
  - The overview film with its "Every figure is sample data" caption (#demo). It shows exactly this job.
  - Proof: "Every vendor bill was typed in twice, into two systems, about 30 a day"; "live about six weeks after the on-site day"; "64 of 67 bills through the agent in week one"; "kept running for a monthly fee" (AP invoice agent card). Client stays "a specialty manufacturer"; systems stay "accounting software + a custom operations database". No product names.
  - AP workbench dashboard: "every open bill, its PO match and its approval state" (portfolio grid).
  - Purchasing and PO write-back section (portfolio grid).
  - Approval and access: "Nothing posts without you", "It touches only its job" (#why).
  - Two page-specific questions: "How long does it take to go live?" and "Who approves what the agent does?" (FAQ answers, verbatim).
- Links: out to `/services/`, `/portfolio/`, `/how-lumic-works/`, `/industries/manufacturing/`, `/st-louis/`; in from home, services hub, portfolio, manufacturing and distribution pages, every systems page (generic link, no proof).
- Schema: Service (serviceType "Accounts payable automation"), VideoObject, BreadcrumbList, FAQPage for its two questions only.
- Needs: nothing beyond a yes to reuse the overview film here.

### Cash receipts and collections `/services/cash-receipts-and-collections/`

- Primary: "cash application automation". Secondary: "remittance entry automation", "collections email automation", "AR aging dashboard". Intent: commercial. Realistic: "cash application" has vendor competition, but the long-tail "remittance" and "collections email" variants are thin.
- Purpose: a controller or AR clerk sees remittances keyed and collections drafted for them, and books a call.
- H1: "Cash receipts entered and collections drafted, ready when the day starts."
- Title: "Cash receipts and collections automation | lumic"
- Meta: "An agent reads remittances and ACH detail, keys them into the ERP, and drafts collections emails from live aging. A person approves and sends every one."
- Content: Cash receipts card ("Remittances and ACH detail, read and keyed into the ERP"; "A person approves each entry"); Collections agent card ("drafts the collections email and the statement for each past-due customer… A person reviews each one and sends it"); Receivables and aging dashboard ("the same view that feeds the collections agent"); the "Cash receipts keyed from remittances" row of the comparison table; the Receivables film.
- Links: out to `/services/`, `/services/dashboards-and-reporting/`, `/portfolio/`, `/industries/distribution/`; in from services hub, distribution page, portfolio.
- Schema: Service, VideoObject (Receivables film), BreadcrumbList.
- Needs: optional. A short, name-free description of how the agent handles a remittance that does not match an open invoice would make the page stronger than the home page cards.

### Payroll `/services/payroll/`

- Primary: "payroll journal entry automation". Secondary: "payroll preparation automation", "payroll to general ledger entry". Intent: commercial. Realistic: low-competition long tail; most payroll content is about running payroll, not booking it.
- Purpose: a controller sees payroll entries prepared and approved, not retyped.
- H1: "Payroll entries prepared by an agent. The controller approves every run."
- Title: "Payroll journal entry automation | lumic"
- Meta: "lumic's payroll agent prepares the payroll entries between payroll and accounting software. The controller approves every run before anything posts."
- Content: Payroll preparation card (portfolio grid); "payroll + accounting software" tag; approval language (#why); the leadership line "Designed the AP, payroll and month-end agents lumic deploys" (#founders) as the finance-trained angle.
- Links: out to `/services/`, `/services/month-end-close/`, `/how-lumic-works/`; in from services hub, portfolio.
- Schema: Service, BreadcrumbList.
- Needs: **yes.** The site has two lines on payroll. Before build, Christian supplies a name-free, step-by-step description of what the payroll agent reads, prepares and hands to the controller. Without it the page is thin; hold it and keep payroll as a hub card.

### Month-end close `/services/month-end-close/`

- Primary: "month-end close automation". Secondary: "month-end journal entry automation", "bank reconciliation automation", "consolidated financials for multiple companies". Intent: commercial. Realistic: the head term is contested; the journal-entry and multi-company variants are not.
- Purpose: a controller sees close entries prepared and approved, with live consolidated results.
- H1: "Month-end entries prepared by an agent, approved before anything posts."
- Title: "Month-end close automation: entries and bank rec | lumic"
- Meta: "An agent prepares the month-end entries and matches bank to book. The controller approves before anything posts, and the results show live."
- Content: Month-end close entries card; Bank reconciliation card ("matches the bank to the book… approval-gated"); Consolidated financials dashboard ("consolidated across sister companies… never stale"); the Financial film; comparison row "Month-end entries built by hand → Prepared by an agent, approved by you".
- Links: out to `/services/`, `/services/dashboards-and-reporting/`, `/services/payroll/`; in from services hub, portfolio, payroll.
- Schema: Service, VideoObject (Financial film), BreadcrumbList.
- Needs: same as payroll, a short name-free description of which entries the agent prepares. The page can ship without it, because the bank rec and consolidation content gives it enough substance.

### Dashboards and reporting `/services/dashboards-and-reporting/`

- Primary: "live ERP dashboards for small business". Secondary: "job costing dashboard", "sales and margin dashboard", "multi-company consolidated reporting", "ask your data AI". Intent: commercial. Realistic: "dashboard" plus a specific report name is long tail; BI vendors own "business dashboards".
- Purpose: an owner who exports the same report every morning sees it live, and books a call.
- H1: "Live dashboards on your own data. No more morning export."
- Title: "Live ERP dashboards and reporting | lumic"
- Meta: "Sales and margin, receivables, purchasing, job costing and consolidated financials, read live from your ERP. Dashboards only read; nothing posts from them."
- Content: the nine dashboards from the portfolio (Sales and margin, Receivables and aging, Consolidated financials, Job costing and production rates, Purchasing, Commissions, PTO tracking, AP workbench, Ask your data); "Dashboards only read" (#why); all five dashboard films with "Every figure is sample data"; "Exporting the same reports every morning → Live dashboards, no export".
- Links: out to `/services/`, `/portfolio/`, `/industries/manufacturing/` (job costing), `/industries/distribution/` (sales and margin); in from home films section, services hub, month-end, cash receipts.
- Schema: Service, VideoObject x5, BreadcrumbList.
- Needs: nothing.

### Portfolio `/portfolio/`

- Primary: "AI agents in production examples". Secondary: "AI back-office automation case study", "AP agent case study". Intent: commercial investigation. Realistic: buyers who compare firms search for examples; little competition from firms of this kind.
- Purpose: prove it runs, then send the reader to the matching service page.
- H1: "In production, every day."
- Title: "Portfolio: AI agents and dashboards in production | lumic"
- Meta: "Agents and live dashboards lumic built, running every day inside operating companies. Clients are kept private; every figure is from production."
- Content: every card now in #proof, moved verbatim: the three lead cards and the full grid. Keep "Clients are kept private; every figure is from production." Each card links to its service page.
- Links: out to every service page; in from home, nav, every service and industry page. Systems pages link here only as a whole, never to a card.
- Schema: CollectionPage with an ItemList of the agents and dashboards (as Service items), BreadcrumbList. No Review or rating markup.
- Needs: nothing.

### Industries

Each industry page shares the method, so each must differ by the jobs and dashboards that matter to that reader. Proof is anonymous and drawn only from the cards. None names a product.

**Manufacturing `/industries/manufacturing/`**
- Primary: "AI automation for manufacturers". Secondary: "AP automation for manufacturers", "job costing dashboard for manufacturers", "manufacturing back-office automation". Intent: commercial. Realistic: the industry + job long tail is thin; "manufacturing AI" alone is not (it is about the shop floor), so the copy must say "back office" early.
- Purpose: a manufacturer's owner or controller sees their own jobs and books a call.
- H1: "AI agents for the manufacturing back office."
- Title: "Back-office AI automation for manufacturers | lumic"
- Meta: "AI agents for a manufacturer's back office: vendor bills matched to POs, job costing during the job, month-end entries. A person approves each entry."
- Content: AP invoice agent card ("a specialty manufacturer", the 64 of 67 proof); Job costing and production rates ("estimate vs. actual per job, during the job"; "Overruns surfaced early"); Purchasing dashboard (vendor price changes); month-end entries.
- Schema: Service (audience BusinessAudience), BreadcrumbList.
- Needs: nothing.

**Distribution `/industries/distribution/`**
- Primary: "AI automation for distributors". Secondary: "distributor sales and margin dashboard", "cash receipts automation for distributors", "multi-company reporting". Intent: commercial. Realistic: same as manufacturing.
- H1: "AI agents for the distribution back office."
- Title: "Back-office AI automation for distributors | lumic"
- Meta: "Cash receipts keyed, collections drafted, and margin by customer, product and rep, live across companies. Each entry waits for a person's approval."
- Content: "A finance team run on agents" card ("a multi-company manufacturer and distributor", "about 13 agent roles", "nine live dashboards"); Sales and margin ("by customer, product and rep… multi-company, one view"); Cash receipts and Collections; Purchasing and PO write-back.
- Difference from manufacturing: leads with receivables, margin by customer and multi-company; manufacturing leads with AP against POs and job costing. The multi-company card appears on both, but only as a supporting line on manufacturing.
- Schema and needs: as manufacturing.

**Service firms `/industries/service-firms/` (phase 4)**
- Primary: "back-office automation for service firms". Secondary: "AP automation for professional services", "collections automation for service businesses". Intent: commercial.
- The site carries no service-firm example today. Built now, it would be method-only and thin.
- Needs: **yes.** An anonymous service-firm example the partners can stand behind, or a decision to ship a method-only page (AP, collections, payroll, approval). Until then, service firms stay a line on the services hub and home.

Industries hub `/industries/` (phase 3): three cards and one paragraph; exists mainly for breadcrumbs. Mark it `noindex` if it stays under about 150 words.

### Systems pages

All systems pages share one template, and each needs content that only fits that system: how lumic reaches it (cloud app vs. desktop software on a dedicated computer), which jobs searchers in that system ask about, and the approval step. No proof numbers, no portfolio cards, no client descriptions, no films (the films show sample data in lumic's own screens; placing them here would suggest they show that product).

**Systems hub `/systems/`**
- Primary: "accounting system automation". Secondary: "ERP automation small business", "AI agent for ERP". Intent: commercial.
- H1: "If your team runs it, lumic can work with it."
- Title: "Systems lumic works with: ERP and accounting | lumic"
- Meta: "lumic's agents work inside the ERP, accounting, payroll, email and spreadsheet tools your team already runs. A person approves before anything posts."
- Content: the full list from `llms.txt` "Systems" inside `[data-systems-list]`; "Where the agent works" tiles (#demo flow section); links to each systems page.

**QuickBooks `/systems/quickbooks/`**
- Primary: "QuickBooks AP automation". Secondary: "QuickBooks Desktop automation", "QuickBooks Online bill entry automation", "QuickBooks AI agent". Intent: commercial. Realistic: "QuickBooks automation" is crowded with apps; "QuickBooks Desktop automation" is underserved, because most apps only reach the online product.
- H1: "AI agents that work in QuickBooks Online and QuickBooks Desktop."
- Title: "QuickBooks automation with AI agents | lumic"
- Meta: "lumic works with QuickBooks Online and Desktop. An agent prepares bills, receipts and entries in QuickBooks, and a person approves before anything posts."
- Content: two sections (Online; Desktop on a dedicated computer under its own login); jobs (AP, cash receipts, month-end entries, live reports), each linking to its service page; approval and access lines (#why).

**NetSuite `/systems/netsuite/`**
- Primary: "NetSuite AP automation". Secondary: "NetSuite AI agent", "NetSuite month-end automation". Intent: commercial. Realistic: NetSuite buyers are mid-market and search job-specific terms; partners compete, but the AI-agent framing is new.
- H1: "AI agents that work in NetSuite."
- Title: "NetSuite automation with AI agents | lumic"
- Meta: "lumic works with NetSuite. An agent prepares vendor bills, cash receipts and close entries in NetSuite, and a person approves before anything posts."

**Sage 100 `/systems/sage-100/`**
- Primary: "Sage 100 automation". Secondary: "Sage 100 AP automation", "Sage 100 dashboards", "Sage 100 real-time reporting". Intent: commercial. Realistic: an older on-premises ERP with a loyal base, weak native reporting and few modern add-ons, so job-specific terms have little competition.
- H1: "AI agents and live dashboards that work with Sage 100."
- Title: "Sage 100 automation and dashboards | lumic"
- Meta: "lumic works with Sage 100. An agent prepares bills, receipts and entries on its own computer, dashboards read live, and a person approves each entry."
- Note: the playbook warns that nothing public may imply Sage 100 is all lumic does. This page sits beside the others, with the same weight.

**Sage Intacct `/systems/sage-intacct/` (phase 4)**
- Primary: "Sage Intacct automation". Secondary: "Sage Intacct AP automation", "Sage Intacct AI agent". Intent: commercial.
- H1: "AI agents that work in Sage Intacct." Title: "Sage Intacct automation with AI agents | lumic"
- Meta: "lumic works with Sage Intacct. An agent prepares bills, cash receipts and close entries in Intacct, and a person approves before anything posts."

Systems pages, shared:
- Links: out to `/systems/`, the matching service pages, `/how-lumic-works/`, `/portfolio/` (whole page only); in from the systems hub and from the home systems list.
- Schema: Service (with `serviceType` naming the job, not the product as a brand claim), BreadcrumbList. No `isRelatedTo` or `brand` that implies a partnership.
- Needs: **yes, for every systems page.** Christian or Josh confirms (1) lumic has real working knowledge of that system, and (2) the honest depth for each job (reads only, prepares entries for approval, or writes after approval) and the route (cloud connection, import, or screens on a dedicated computer). The page states only what they confirm. Also needs their yes on the `qa.py` exception below.

### St. Louis `/st-louis/` (phase 1)

- Primary: "AI automation St. Louis". Secondary: "AI consultant St. Louis", "accounting automation St. Louis", "back-office automation St. Louis MO". Intent: local. Realistic: local service terms have few strong competitors, and the site already lists the counties served.
- Purpose: a St. Louis owner sees a local team that comes on site, and books a call or a visit.
- H1: "Forward Deployed Engineers in St. Louis. On site, where the work happens."
- Title: "AI automation in St. Louis: on-site FDEs | lumic"
- Meta: "lumic's FDEs are based in St. Louis and work on site beside your team, from vendor bills to month-end. St. Louis first; lumic travels for the right fit."
- Content: area served (llms.txt "Area served": St. Louis City, St. Louis County, St. Charles, Jefferson and Franklin Counties in Missouri; Madison and St. Clair Counties in Illinois); "On-site diagnostic" (#how); "What happens next" three steps, ending in the on-site visit (#contact); "Do you work outside St. Louis?" answer; links to the AP page and portfolio for proof; contact block.
- Links: out to `/services/ap-automation/`, `/portfolio/`, `/how-lumic-works/`; in from home footer ("Serving Greater St. Louis"), How lumic works, AP page.
- Schema: references `#org` (ProfessionalService, a LocalBusiness subtype) with `areaServed` as today; no street address (service-area business); BreadcrumbList.
- Needs: Christian's decision on the Google Business Profile (draft in the playbook, `brand/google-business-profile-draft.md`), so name, area and site match exactly. A photo of on-site work would help, only with the people's and the business's permission.

### How lumic works `/how-lumic-works/` (phase 1)

- Primary: "forward deployed engineers for small business". Secondary: "what is a forward deployed engineer", "FDE firm", "AI agent approval workflow", "AI agent data security". Intent: informational. Realistic: "forward deployed engineer" searches are rising and the results are job posts and enterprise firms; the small-business angle is open.
- Purpose: answer "how does this work and is it safe" so the reader trusts lumic enough to book.
- H1: "How lumic works: Forward Deployed Engineers, one job at a time."
- Title: "How lumic works: FDEs, approvals and data security | lumic"
- Meta: "lumic's FDEs work on site, build one agent per job and keep it working. Each agent touches only its job, every action is logged, nothing posts without you."
- Content: FDE definition ("What is an FDE?" answer); the three steps (#how); "Deploy an agent" and "Managed AI agents" detail (#services); approval gates ("Nothing posts without you"); security and data ("It runs where it fits", "It touches only its job", "To read a document, it uses a cloud AI model"); "Finance people who code" (#why); the right-fit lines from llms.txt ("may not be the right fit for buyers who want a self-serve software license… or an agent that acts with no person approving"); leadership at `#leadership` (#founders bios as written, with LinkedIn links); "How the data flows" chart if moved off home.
- Links: out to `/services/`, `/portfolio/`, `/faq/`, `/st-louis/`; in from every page (nav).
- Schema: AboutPage, Person x2 (existing), BreadcrumbList.
- Needs: Josh (he leads "how each agent handles your data") to confirm the security lines and anything added beyond the site's current wording, such as data retention or which AI provider is used. Without new lines, the page uses only today's wording.

### FAQ `/faq/`

- Primary: "what is a forward deployed engineer". Secondary: "who approves AI agent entries", "how long to deploy an AI agent", "where does an AI agent run". Intent: informational. Realistic: question terms with few direct answers from small firms; also the page AI assistants cite.
- Purpose: remove the last doubts and point to a call.
- H1: "Common questions about lumic."
- Title: "FAQ: FDEs, AI agents and approvals | lumic"
- Meta: "What an FDE is, where the agent runs, what it can touch, who approves its work, how long it takes to go live, and how lumic prices a job."
- Content: the seven current FAQ answers, verbatim. New questions only where the answer already exists on the site: "Does lumic sell software?" (#services: "lumic does not sell software to configure yourself"); "What happens after an agent goes live?" (Managed AI agents card); "What systems does lumic work with?" (link to `/systems/`); "Is lumic the right fit?" (llms.txt right-fit lines).
- Schema: FAQPage (the master; each question is marked up on one page only), BreadcrumbList. Google shows FAQ rich results only for a small set of sites since 2023, so the value here is clarity and AI citation, not a rich result.
- Needs: nothing.

## Nav and footer

- Primary nav (desktop): Services (menu: the five service pages), Portfolio, Systems, How lumic works, St. Louis, plus the "Book a call" button. Mobile: the same, in one menu. "Demo" and "Leadership" leave the nav; Demo stays on home, Leadership moves to How lumic works.
- Anchor links (`#services`, `#proof`) become page links on every page. On home, the old anchors stay in place so old links still land.
- Footer: four short columns. Services (five pages), Industries (manufacturing, distribution), Systems (hub plus each systems page), Company (How lumic works, Portfolio, FAQ, St. Louis, Privacy, LinkedIn). Keep the bottom line: "© 2026 lumic · Serving Greater St. Louis, Missouri and Illinois · Privacy". Product names in the footer are a QA question: link the systems pages in the footer as "Systems" only, or extend the QA allowlist to footer links (recommended: "Systems" only, to keep the rule simple).
- Every inner page gets a visible breadcrumb that matches its BreadcrumbList.

## Films and the sample-data note

- Home keeps both 16:9 players (#why-film, #overview-film) and "Watch each tool on its own".
- Reuse, never copy: the AP page embeds the overview film; dashboards embeds all five tool films; cash receipts embeds Receivables; month-end embeds Financial. Same files in `/video/`, so there is one source.
- Every embed carries "Every figure is sample data." directly under the player, as on home. Make it part of the shared film component, so a page cannot show a film without it.
- One film with sound at a time, on every page (move the current player script to a shared file).
- No films on systems, industry or St. Louis pages.
- Add VideoObject markup (name, description, thumbnailUrl from the existing poster, contentUrl, uploadDate) on each page that embeds a film.

## Building many pages without a framework

The stack stays vanilla: static HTML, one CSS file, one small JS file, Python build scripts. No bundler.

- Move the inline CSS and the film and nav script into `/site.css` and `/site.js`.
- Add `scripts/pages.json`: one entry per page (path, title, meta description, H1, priority, nav group, parent for breadcrumbs, film list, `system` family for systems pages, `indexable`).
- Add a small `scripts/build_pages.py` that stamps the shared head (title, meta, canonical, Open Graph, JSON-LD), nav, breadcrumb and footer around each page body (`src/pages/<slug>.html`) and writes `public/<slug>/index.html`. Home stays hand-edited in `public/index.html`, with the shared parts stamped in.

### `build_markdown.py` and `llms.txt`

- Loop over every indexable page in `pages.json`, not only `index.html`. Write `public/<slug>/index.md` next to each page, with the same front matter (title, description, canonical, last_updated).
- Scope the systems-list rewrite (the full list from `llms.txt`) to home and `/systems/`.
- Read the FAQ from `/faq/` JSON-LD, not home.
- `llms.txt`: keep the hand-written summary. Generate its "Pages" section from `pages.json` (one line per page: link and a one-line purpose), plus the markdown link of each page.
- `llms-full.txt`: `llms.txt`, then every page's markdown in nav order.
- `schema.jsonld`: one combined `@graph` of all pages (one Organization, `@id` `#org`, referenced by every Service). `schemamap.xml` stays one entry.
- `.well-known/ard.json`: add one entry per markdown page; keep the "only files that exist" assert.
- `src/worker.js`: replace the fixed `MD_PAGES` map with a rule: a page path with `Accept: text/markdown` or `?mode=agent` returns `<path>index.md` if it exists. The `Link` header points to each page's own markdown copy.

## Canonical, sitemap.xml and IndexNow

- Canonical: every page self-canonical, absolute, with the trailing slash (`html_handling` is `auto-trailing-slash`). `og:url` matches the canonical. `/about/` 301s to `/how-lumic-works/` in the worker, as the existing 301s do.
- `sitemap.xml`: generated by `build_pages.py` from `pages.json` (indexable pages only), with `lastmod` from each source file's last git commit date, not the build date, so unchanged pages do not look changed.
- IndexNow: the key file is already live (`public/3f290be1e1f3e1b01472e6833d0d9098.txt`). Add `scripts/indexnow.py`, run after each deploy: it posts the URLs whose `lastmod` changed to `api.indexnow.org` (Bing, Yandex and others). Alternative: turn on Cloudflare Crawler Hints, which sends IndexNow pings itself. Pick one, not both.
- Google does not use IndexNow: submit `sitemap.xml` in Search Console (the property is verified by `google90d029398c07d404.html`) and request indexing for each new page with URL Inspection.

## Thin-content and duplicate risk

Highest risk: systems pages (four pages with the same template and no proof) and the two industry pages (shared method, shared multi-company card).

How each page stays distinct:
- Systems pages: each carries content only true of that system: cloud or desktop, the route lumic uses, the jobs its users search for, and its own Q and A. The shared method (approval, access, logging) is one short block, linked to `/how-lumic-works/` rather than repeated. Target at least 60% unique text per systems page; check with a simple text-overlap script before publish.
- QuickBooks: two products in one page, the desktop angle. NetSuite: mid-market cloud ERP, multi-entity close. Sage 100: on-premises, a dedicated computer, live dashboards over weak native reports. Sage Intacct: cloud, dimensions and multi-entity; held until it differs enough from NetSuite.
- Industry pages: manufacturing leads with AP against POs and job costing; distribution leads with receivables, margin by customer and rep, and multi-company. Service firms wait for real content.
- Service pages: each owns one job and its films; the comparison table row for that job appears only on its page and the hub.
- FAQ markup: each question marked up on one page only.
- Watch Search Console for "Crawled, currently not indexed" or "Duplicate, Google chose different canonical" on these pages. If a page shows it after eight weeks, merge it into its hub or `noindex` it.

## QA changes (`scripts/qa.py`)

Today `qa.py` checks only `/`, expects exactly two film players, and allows product names only as list items inside the one `[data-systems-list]`. The private banned list also bans `Sage`, `QuickBooks` and `FileMaker` everywhere outside that list.

Proposed:
- Read `pages.json` and run the common checks (no horizontal scroll at all widths, in-page links have targets, banned terms, media answer 200) on every page. Keep the film checks, but key them to the films each page declares.
- Scoped product-name exception: on a page whose `pages.json` entry has `system: "quickbooks"`, the patterns for that family only (`QuickBooks Online`, `QuickBooks Desktop`, `\bQuickBooks\b`) are allowed in `<main>` and in the title and meta. Every other product name still fails on that page. The systems hub keeps the one `[data-systems-list]` rule. Client and employer names stay banned everywhere, including systems pages.
- Proof guard on `/systems/*`: fail if the page contains any proof string ("64 of 67", "six weeks", "13 agent roles", "nine live dashboards", "specialty manufacturer", "multi-company manufacturer", "30 a day") or a link to a portfolio card anchor.
- Product guard on every non-systems page except home: no product name at all, even in links.
- A sitemap check: every URL in `sitemap.xml` returns 200 and has a matching canonical.

## Build order

**Phase 1 (first three pages, plus the home trim):**
1. `/services/ap-automation/`: the strongest proof on the site, a film that shows exactly this job, and the highest commercial intent. It is the page most likely to turn a search into a call.
2. `/st-louis/`: local terms are the most realistic ranking for a new domain, the content already exists, and it supports the Google Business Profile.
3. `/how-lumic-works/`: every other page links here for method, approvals and security; "forward deployed engineers for small business" has little competition; it takes the leadership section off home.

Phase 1 also needs the shared CSS, JS, `pages.json`, the extended `build_markdown.py`, sitemap and the worker markdown rule. Until `/services/` exists, the AP page breadcrumb points to home.

**Phase 2:** services hub, month-end, cash receipts and collections, dashboards, portfolio, FAQ; payroll once its description is in.
**Phase 3:** the `qa.py` scoped exception first, then systems hub, QuickBooks, NetSuite, Sage 100, then the industries hub, manufacturing and distribution.
**Phase 4:** Sage Intacct, service firms, and a check on Business Central and Acumatica.

## Measuring results

Search Console (monthly, per page group):
- Indexing: each new page indexed within about two weeks; no "Crawled, currently not indexed".
- Impressions first (weeks 2 to 8), then clicks and CTR. For a new domain, impressions on long-tail terms are the first sign a page works.
- Queries per page group with regex filters, for example `(?i)st\.? ?louis` for the local page and `(?i)(accounts payable|vendor bill|invoice)` for AP. Add terms that appear and that the page does not yet answer.
- Average position for each primary keyword; below position 30 after three months means the term is too broad, so shift to the longer variant.

Cloudflare Web Analytics:
- Not on the site today (no beacon in `index.html`). Turn it on for get-lumic.com (automatic setup, or the beacon snippet in the shared head). It is cookieless, so no consent banner; add one line to `/privacy/`.
- Watch views per path, entry pages, and referrers (Google, Bing, AI assistants).
- Bookings by page: add the source page as a query parameter to each "Book a call" link (confirm cal.com keeps it on the booking), so each booked call shows the page it came from.

Review at 30, 60 and 90 days after each phase. Decide per page: keep, extend, merge or `noindex`.

## Needs from Christian or Josh, in one list

- AP page: a yes to reuse the overview film there.
- Payroll and month-end: a name-free, step-by-step description of what each agent prepares (payroll is held until this arrives).
- Every systems page: confirmation of real working knowledge and of the honest depth and route per job; a yes on the `qa.py` scoped exception.
- Sage Intacct: enough distinct, confirmed content to differ from NetSuite.
- Service firms: an anonymous example, or a decision to ship method-only.
- St. Louis: the Google Business Profile decision, so the listing and the page match.
- How lumic works: Josh confirms the security and data lines, and any new ones.
- Measurement: turn on Cloudflare Web Analytics and pick IndexNow by script or by Crawler Hints.
