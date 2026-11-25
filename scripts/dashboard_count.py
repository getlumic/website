"""How many live dashboards lumic runs, counted from the code (Christian 2026-11-25: "Always use the code for dashboard
count ... they all count so go by the code and keep it fresh").

One dashboard = one app with its own UI that runs in production (a Flask app or a dashboard package). Agents, scripts,
demos and sample apps are not counted. Recount from the dashboard registries and app folders in the private repos, then
change COUNT and COUNTED below and rebuild: build_pages.py writes the number, as a word, into every "<n> live dashboards".

Counted 2026-11-25 (18): receivables, sales, purchasing, financial, batch workbench, order entry, commissions, PTO,
production sheet builder, margins, customer service, employee ownership, freight, payables intake, production rates,
payables review, order desk, payroll.
"""
COUNT = 18
COUNTED = "2026-11-25"

_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
          "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "twenty-one",
          "twenty-two", "twenty-three", "twenty-four", "twenty-five", "twenty-six", "twenty-seven", "twenty-eight",
          "twenty-nine", "thirty"]
WORD = _WORDS[COUNT]  # "eighteen"; the sentence around it decides the capital letter
NUMBER_WORDS = _WORDS[1:]
