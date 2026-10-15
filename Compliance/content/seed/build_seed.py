#!/usr/bin/env python3
"""Builds the v0 obligation seed library (content/seed/obligations.seed.json) and the register
table in docs/COMPLIANCE_UNIVERSE.md from ONE compact definition, so the docs, the prototype and
the first content packs (tasks T06-T08) never drift apart.

    python content/seed/build_seed.py

STATUS OF THIS CONTENT: drafted by an AI acting as a compliance auditor, from knowledge up to
mid-2026 plus spot checks (labour codes in force 21-Nov-2025, DPDP Rules Nov-2025, Boilers Act
2025, Income-tax Act 2025). Every item is `review: "sme_pending"`. Items with `verify: True` have
a specific fact (date, threshold, form number) that MUST be checked against the source before a
pack is published. The packs built in T06-T08 re-verify every item with a cited source.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------- facts (profile questions)
FACTS = {
    "state": {"label": "State", "type": "enum", "options": ["MH", "OD", "GJ", "KA", "DL"]},
    "legal_form": {"label": "Legal form", "type": "enum",
                   "options": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"]},
    "sectors": {"label": "Sectors", "type": "set",
                "options": ["manufacturing", "healthcare", "construction", "electrical"]},
    "employees": {"label": "Directly employed workers", "type": "int"},
    "contract_workers": {"label": "Contract workers", "type": "int"},
    "total_workers": {"label": "Total workers (direct + contract)", "type": "int", "derived": True},
    "uses_power": {"label": "Manufacturing process uses power", "type": "bool"},
    "hazardous_process": {"label": "Hazardous process (OSH Code schedule)", "type": "bool"},
    "gst_registered": {"label": "GST registered", "type": "bool"},
    "gst_qrmp": {"label": "GST QRMP scheme (quarterly returns)", "type": "bool"},
    "turnover_cr": {"label": "Annual turnover (₹ crore)", "type": "number"},
    "pcb_category": {"label": "Pollution category (Red/Orange/Green/White)", "type": "enum",
                     "options": ["red", "orange", "green", "white"]},
    "hazardous_waste": {"label": "Generates hazardous waste", "type": "bool"},
    "plastic_packaging": {"label": "Uses plastic packaging for products (PIBO)", "type": "bool"},
    "ewaste_bulk": {"label": "Bulk consumer of electrical & electronic equipment", "type": "bool"},
    "dg_set_kva": {"label": "DG set capacity (kVA)", "type": "number"},
    "has_boiler": {"label": "Steam boiler on premises", "type": "bool"},
    "has_pressure_vessel": {"label": "Air receivers / pressure vessels", "type": "bool"},
    "has_lifting": {"label": "Hoists, cranes, lifting tackles", "type": "bool"},
    "has_lift": {"label": "Passenger / goods lift", "type": "bool"},
    "fire_noc_required": {"label": "Premises needs Fire NOC (height ≥ 15 m, hospital, factory, assembly)", "type": "bool"},
    "ht_installation": {"label": "HT electrical installation (> 650 V)", "type": "bool"},
    "electrical_contractor": {"label": "Business holds an electrical contractor licence", "type": "bool"},
    "weighing_instruments": {"label": "Uses weighing/measuring instruments in trade", "type": "bool"},
    "packaged_goods": {"label": "Manufactures/packs pre-packaged commodities", "type": "bool"},
    "beds": {"label": "In-patient beds", "type": "int"},
    "xray_units": {"label": "X-ray / CT / C-arm units", "type": "int"},
    "ultrasound_units": {"label": "Ultrasound (USG) machines", "type": "int"},
    "pharmacy": {"label": "In-house pharmacy", "type": "bool"},
    "ndps_stock": {"label": "Stocks essential narcotic drugs (morphine etc.)", "type": "bool"},
    "blood_centre": {"label": "Blood centre / storage unit", "type": "bool"},
    "construction_active": {"label": "Running building/construction work", "type": "bool"},
    "construction_workers": {"label": "Construction workers on site (peak)", "type": "int"},
    "rera_project": {"label": "Registered RERA project", "type": "bool"},
    "owes_mse_suppliers": {"label": "Buys from Micro/Small enterprises", "type": "bool"},
}


def F(fact, op, value=True):
    return {"fact": fact, "op": op, "value": value}


def ALL(*c):
    return {"all": list(c)}


def ANY(*c):
    return {"any": list(c)}


ALWAYS = {"all": []}
MH = F("state", "eq", "MH")
COMPANY = F("legal_form", "in", ["pvt_ltd", "public_ltd"])
SEC = lambda s: F("sectors", "contains", s)  # noqa: E731

# --------------------------------------------------------------------------- obligations
# (id, title, category, law, authority, jur, freq, due, due_rule, risk, applies, inputs,
#  evidence, owner, workflow, ai, source, verify, penalty)
O: list[dict] = []


def ob(id, title, cat, law, authority, jur, freq, due, rule, risk, applies, inputs, evidence,
       owner, wf="standard", ai=(), src="", verify=False, penalty="", audit=""):
    O.append(dict(id=id, title=title, category=cat, law=law, authority=authority,
                  jurisdiction=jur, frequency=freq, due=due, due_rule=rule, risk=risk,
                  applies=applies, inputs=list(inputs), evidence=list(evidence),
                  owner_role=owner, workflow=wf, ai_templates=list(ai), source_url=src,
                  verify=verify, penalty=penalty, audit_point=audit, review="sme_pending"))


# ---- Labour & social security (labour codes in force from 21-Nov-2025)
ob("IN.SS.EPF.ECR", "EPF monthly ECR & contribution payment", "social_security",
   "Code on Social Security, 2020 (EPF scheme)", "EPFO", "IN", "monthly",
   "15th of following month", {"type": "monthly_day", "day": 15}, "H",
   F("employees", "gte", 20),
   ["Monthly payroll: gross, basic+DA, PF wages per employee", "UAN list, joiners/leavers",
    "Excluded allowances (50% wage rule check)"],
   ["ECR file", "TRRN challan", "Bank payment confirmation"], "maker:hr",
   ai=["pf_working"], src="https://www.epfindia.gov.in",
   penalty="Interest + damages on delayed remittance; prosecution for deducted-but-not-paid",
   audit="Recompute 2 months of PF on wages per Code on Wages 2(y) 50% rule; tie TRRN to bank")
ob("IN.SS.ESI.MC", "ESI monthly contribution", "social_security",
   "Code on Social Security, 2020 (ESI)", "ESIC", "IN", "monthly",
   "15th of following month", {"type": "monthly_day", "day": 15}, "H",
   F("employees", "gte", 10),
   ["Payroll: gross wages per employee", "Eligible employees (wages ≤ ESI ceiling)",
    "Days paid"], ["ESI challan", "Monthly contribution statement"], "maker:hr",
   ai=["esi_working"], src="https://www.esic.gov.in",
   penalty="Interest + damages; loss of benefits to employees",
   audit="Check all employees ≤ wage ceiling are covered; joiners registered within 10 days")
ob("IN.SS.JOIN", "Register new joiners (UAN / ESI IP) and issue appointment letter",
   "labour", "OSH Code 2020 s.6(1)(f); Code on Social Security", "EPFO / ESIC", "IN", "event",
   "Within 10 days of joining (ESI); appointment letter at joining",
   {"type": "event_within", "event": "employee_joined", "days": 10}, "M",
   F("employees", "gte", 10),
   ["Joiner details (KYC, Aadhaar-linked)", "Designation, wages, terms"],
   ["Appointment letter (signed copy)", "UAN / ESI IP number"], "maker:hr", wf="fast",
   ai=["appointment_letter"], src="https://labour.gov.in", verify=True)
ob("IN.WAGE.PAY", "Pay monthly wages by the statutory date", "labour",
   "Code on Wages, 2019 s.17", "Inspector-cum-Facilitator", "IN", "monthly",
   "7th of following month (monthly wage period)", {"type": "monthly_day", "day": 7}, "H",
   F("employees", "gte", 1),
   ["Payroll register", "Bank transfer file"], ["Bank statement / payment advice", "Wage slips"],
   "maker:accounts", src="https://labour.gov.in",
   penalty="Fine up to ₹50,000 (first offence), higher for repeat",
   audit="Sample 3 months: payment date ≤ 7th; wage slips issued")
ob("IN.WAGE.FNF", "Full & final settlement within 2 working days of exit", "labour",
   "Code on Wages, 2019 s.17(2)", "Inspector-cum-Facilitator", "IN", "event",
   "2 working days from removal / dismissal / resignation",
   {"type": "event_within", "event": "employee_exited", "days": 2, "working_days": True}, "M",
   F("employees", "gte", 1), ["Exit date, dues computation"], ["F&F statement, bank advice"],
   "maker:hr", wf="fast", src="https://labour.gov.in")
ob("IN.WAGE.MINREV", "Minimum wage / VDA revision check", "labour",
   "Code on Wages, 2019; state minimum wage notifications", "State Labour Dept", "IN",
   "half_yearly", "On each VDA revision (MH: Jan & Jul)",
   {"type": "dates", "dates": ["01-15", "07-15"]}, "M", F("employees", "gte", 1),
   ["Current wage master by skill category", "Latest notification"],
   ["Revision working", "Approved wage master"], "maker:hr", ai=["min_wage_gap"],
   src="https://labour.gov.in", verify=True)
ob("IN.WAGE.BONUS", "Statutory bonus payment", "labour", "Code on Wages, 2019 (bonus)",
   "Inspector-cum-Facilitator", "IN", "annual",
   "Within 8 months of close of accounting year (30 Nov)",
   {"type": "annual", "month": 11, "day": 30}, "M", F("employees", "gte", 20),
   ["Allocable surplus working", "Eligible employees & wages"], ["Bonus register", "Payment proof"],
   "maker:accounts", ai=["bonus_working"], src="https://labour.gov.in")
ob("IN.LAB.REG", "Maintain registers (employees, wages, attendance, OT, deductions)",
   "labour", "Labour codes + central/state rules (electronic registers)",
   "Inspector-cum-Facilitator", "IN", "continuous", "Updated each wage period",
   {"type": "monthly_selfcheck"}, "M", F("employees", "gte", 1),
   ["HRMS / attendance export"], ["Register extracts (monthly)"], "maker:hr",
   ai=["register_from_payroll"], src="https://labour.gov.in", verify=True,
   audit="Inspect registers for 2 sampled months; cross-check with payroll")
ob("IN.LAB.ANNRET", "Annual return under labour codes", "labour",
   "Labour codes — central/state rules (single electronic return)", "Shram Suvidha / state portal",
   "IN", "annual", "As notified in rules (verify date)", {"type": "annual", "month": 2, "day": 1},
   "M", F("employees", "gte", 10), ["Annual headcount, wages, leave, accidents, bonus data"],
   ["Return acknowledgement"], "maker:hr", ai=["annual_return_worksheet"],
   src="https://shramsuvidha.gov.in", verify=True)
ob("IN.OSH.EREG", "Registration of establishment (OSH Code)", "labour",
   "OSH Code, 2020 s.3", "Registering Officer", "IN", "one_time",
   "Before / on applicability; update changes within prescribed time",
   {"type": "one_time"}, "H", F("total_workers", "gte", 10),
   ["Establishment details, employer, nature of work, headcount incl. contract"],
   ["Registration certificate"], "maker:hr", wf="high_risk", src="https://labour.gov.in",
   verify=True)
ob("IN.OSH.FACLIC", "Factory licence (OSH Code) — renewal", "labour",
   "OSH Code, 2020 (factory licence) + state rules", "Chief Inspector-cum-Facilitator", "IN",
   "renewal", "Before expiry", {"type": "before_expiry", "licence": "factory_licence", "days": 60},
   "H", ALL(SEC("manufacturing"), ANY(ALL(F("uses_power", "eq"), F("total_workers", "gte", 20)),
                                       F("total_workers", "gte", 40))),
   ["Licence details, max workers, power (HP/kW), plans if changed"],
   ["Licence copy", "Renewal acknowledgement"], "maker:ehs", wf="high_risk",
   src="https://labour.gov.in", verify=True,
   penalty="Running an unlicensed factory — penalty and prosecution",
   audit="Actual headcount and power vs licensed limits")
ob("IN.OSH.HEALTH", "Annual free health check-up (employees above prescribed age)", "labour",
   "OSH Code, 2020 s.6(1)(c)", "Inspector-cum-Facilitator", "IN", "annual",
   "Once a year", {"type": "annual", "month": 3, "day": 31}, "M", F("total_workers", "gte", 10),
   ["List of employees above prescribed age", "Empanelled clinic"],
   ["Health check records / certificates"], "maker:hr", verify=True)
ob("IN.OSH.SAFEOFF", "Safety officer appointment", "labour", "OSH Code, 2020 + state rules",
   "Inspector-cum-Facilitator", "IN", "continuous", "Maintain at all times",
   {"type": "monthly_selfcheck"}, "H",
   ANY(ALL(SEC("manufacturing"), F("total_workers", "gte", 500)),
       ALL(SEC("construction"), F("construction_workers", "gte", 250)),
       F("hazardous_process", "eq")),
   ["Appointed officer, qualification"], ["Appointment letter, qualification proof"],
   "maker:ehs", verify=True)
ob("IN.SS.CRECHE", "Crèche facility", "labour", "Code on Social Security, 2020 (maternity benefit)",
   "Inspector-cum-Facilitator", "IN", "continuous", "Maintain at all times",
   {"type": "monthly_selfcheck"}, "L", F("employees", "gte", 50),
   ["Crèche arrangement (own/shared)"], ["Agreement / photos / register"], "maker:hr")
ob("IN.CLB.PE", "Principal employer: verify contractors' licence, wages, PF & ESI monthly",
   "labour", "OSH Code, 2020 Ch. XI (contract labour); Code on Wages (principal employer liability)",
   "Inspector-cum-Facilitator", "IN", "monthly", "Before releasing contractor bill (monthly)",
   {"type": "monthly_day", "day": 20}, "H", F("contract_workers", "gt", 0),
   ["Contractor wage sheet", "Contractor PF ECR + challan", "ESI challan", "Gate attendance"],
   ["Reconciliation sheet", "Contractor challans"], "maker:hr", ai=["contractor_recon"],
   src="https://labour.gov.in", verify=True,
   penalty="Principal employer liable for unpaid wages/contributions of contract workers",
   audit="Gate attendance vs ECR member count, 2 contractors × 2 months")
ob("IN.SS.GRAT", "Gratuity payment within 30 days & nominations", "social_security",
   "Code on Social Security, 2020 (gratuity)", "Controlling Authority", "IN", "event",
   "Within 30 days of becoming payable", {"type": "event_within", "event": "employee_exited",
                                          "days": 30}, "M", F("employees", "gte", 10),
   ["Service period, last wages", "Nomination form"], ["Payment proof"], "maker:hr", wf="fast",
   src="https://labour.gov.in")
ob("IN.POSH.IC", "POSH: Internal Committee constituted & policy displayed", "posh",
   "POSH Act, 2013 s.4", "District Officer", "IN", "continuous", "Maintain; reconstitute on change",
   {"type": "monthly_selfcheck"}, "H", F("employees", "gte", 10),
   ["IC members incl. external member", "Policy"], ["IC constitution order", "Policy & notice"],
   "maker:hr", ai=["posh_policy", "posh_notice"], src="https://wcd.nic.in",
   penalty="Fine up to ₹50,000; licence cancellation on repeat")
ob("IN.POSH.AR", "POSH annual report (IC → employer → District Officer)", "posh",
   "POSH Act, 2013 s.21; POSH Rules r.14", "District Officer", "IN", "annual",
   "Calendar year report — typically by 31 Jan (state practice)",
   {"type": "annual", "month": 1, "day": 31}, "M", F("employees", "gte", 10),
   ["Complaints received/disposed, workshops held"], ["Annual report", "Submission proof"],
   "maker:hr", ai=["posh_annual_report"], verify=True)
ob("IN.IR.GRC", "Grievance Redressal Committee", "labour", "Industrial Relations Code, 2020 s.4",
   "Inspector-cum-Facilitator", "IN", "continuous", "Maintain", {"type": "monthly_selfcheck"},
   "L", F("employees", "gte", 20), ["Members (equal employer/worker)"], ["Constitution note"],
   "maker:hr")
ob("IN.IR.SO", "Standing orders", "labour", "Industrial Relations Code, 2020", "Certifying Officer",
   "IN", "one_time", "On applicability", {"type": "one_time"}, "L", F("employees", "gte", 300),
   ["Model standing orders adoption"], ["Certified / adopted standing orders"], "maker:hr")
ob("IN.LAB.DISPLAY", "Statutory notices & abstracts displayed (bilingual)", "labour",
   "Labour codes + rules (wages, hours, holidays, safety, POSH)", "Inspector-cum-Facilitator",
   "IN", "continuous", "Maintain; update on revision", {"type": "monthly_selfcheck"}, "L",
   F("employees", "gte", 1), ["Current wage rates, shift timings, holiday list, IC details"],
   ["Photo of notice board (dated)"], "site_user", wf="fast",
   ai=["display_notices_bilingual"], verify=True)
# ---- Maharashtra labour
ob("MH.LWF", "Maharashtra Labour Welfare Fund contribution", "labour",
   "Maharashtra Labour Welfare Fund Act, 1953", "MLWB", "IN-MH", "half_yearly",
   "June & December contributions by 15 Jul / 15 Jan", {"type": "dates", "dates": ["07-15", "01-15"]},
   "L", ALL(MH, F("employees", "gte", 5)), ["Employees on roll on 30 Jun / 31 Dec"],
   ["Challan", "Return"], "maker:accounts", src="https://public.mlwb.in", verify=True)
ob("MH.PT.PTRC", "Professional Tax (PTRC) — deduct, pay & return", "tax",
   "Maharashtra State Tax on Professions, Trades, Callings and Employments Act, 1975",
   "Maharashtra GST Dept", "IN-MH", "monthly",
   "Last day of month (monthly if previous-year liability ≥ ₹50,000; else annual by 31 Mar)",
   {"type": "month_end"}, "M", ALL(MH, F("employees", "gte", 1)),
   ["Salary slabs per employee"], ["PTRC challan & return"], "maker:accounts",
   src="https://mahagst.gov.in", verify=True)
ob("MH.PT.PTEC", "Professional Tax (PTEC) — enterprise's own tax", "tax",
   "Maharashtra Profession Tax Act, 1975", "Maharashtra GST Dept", "IN-MH", "annual", "30 June",
   {"type": "annual", "month": 6, "day": 30}, "L", MH, ["PTEC number"], ["Challan"],
   "maker:accounts", src="https://mahagst.gov.in", verify=True)
ob("MH.SE.REG", "Shops & Establishments registration / intimation", "labour",
   "Maharashtra Shops and Establishments (Regulation of Employment and Conditions of Service) Act, 2017",
   "Facilitator (Labour Dept)", "IN-MH", "one_time",
   "Registration (≥10 workers) or intimation (<10); changes within prescribed time",
   {"type": "one_time"}, "M", ALL(MH, F("sectors", "not_contains", "manufacturing")),
   ["Establishment details, headcount"], ["Registration certificate / intimation receipt"],
   "maker:hr", src="https://mahakamgar.maharashtra.gov.in", verify=True)
# ---- Tax & corporate
ob("IN.TDS.DEP", "TDS deposit", "tax", "Income-tax Act, 2025 (from 1-Apr-2026)", "Income Tax Dept",
   "IN", "monthly", "7th of following month (March deductions: 30 April)",
   {"type": "monthly_day", "day": 7, "exceptions": {"04": "04-30"}}, "H", ALWAYS,
   ["TDS deducted by section (salary, contractors, rent, professional)"],
   ["Challan (CIN)"], "maker:accounts", src="https://www.incometax.gov.in",
   penalty="Interest per month of delay; disallowance of expense")
ob("IN.TDS.RET", "Quarterly TDS statements", "tax",
   "Income-tax Act, 2025 — new form numbers under Income-tax Rules, 2026", "Income Tax Dept / TRACES",
   "IN", "quarterly", "31 Jul · 31 Oct · 31 Jan · 31 May",
   {"type": "dates", "dates": ["07-31", "10-31", "01-31", "05-31"]}, "H", ALWAYS,
   ["Deductee-wise TDS data", "Challans"], ["Statement acknowledgement (token)"],
   "maker:accounts", src="https://www.incometax.gov.in", verify=True,
   penalty="Late fee per day + penalty for non-filing")
ob("IN.GST.R1", "GSTR-1 (monthly)", "tax", "CGST Act, 2017", "GSTN", "IN", "monthly", "11th",
   {"type": "monthly_day", "day": 11}, "H", ALL(F("gst_registered", "eq"), F("gst_qrmp", "eq", False)),
   ["Sales register / e-invoices"], ["GSTR-1 ARN"], "maker:accounts", ai=["gst_recon"],
   src="https://www.gst.gov.in", penalty="Late fee per day; blocks e-way bill / ITC for buyers")
ob("IN.GST.3B", "GSTR-3B (monthly) & tax payment", "tax", "CGST Act, 2017", "GSTN", "IN",
   "monthly", "20th", {"type": "monthly_day", "day": 20}, "H",
   ALL(F("gst_registered", "eq"), F("gst_qrmp", "eq", False)),
   ["Output tax, ITC per GSTR-2B reconciliation"], ["GSTR-3B ARN", "Payment challan"],
   "maker:accounts", wf="high_risk", ai=["gst_recon"], src="https://www.gst.gov.in",
   penalty="Interest 18% p.a. + late fee")
ob("IN.GST.QRMP", "GST QRMP: PMT-06 monthly, GSTR-1 & 3B quarterly", "tax", "CGST Act, 2017",
   "GSTN", "IN", "monthly", "PMT-06 by 25th; GSTR-1 by 13th and 3B by 22nd/24th after quarter",
   {"type": "monthly_day", "day": 25}, "M", ALL(F("gst_registered", "eq"), F("gst_qrmp", "eq")),
   ["Sales & ITC data"], ["Challans, ARNs"], "maker:accounts", src="https://www.gst.gov.in")
ob("IN.GST.9", "GSTR-9 annual return", "tax", "CGST Act, 2017 s.44", "GSTN", "IN", "annual",
   "31 December", {"type": "annual", "month": 12, "day": 31}, "M",
   ALL(F("gst_registered", "eq"), F("turnover_cr", "gt", 2)), ["Annual books vs returns recon"],
   ["GSTR-9 ARN"], "maker:accounts", src="https://www.gst.gov.in")
ob("IN.IT.ADV", "Advance tax instalments", "tax", "Income-tax Act, 2025", "Income Tax Dept", "IN",
   "quarterly", "15 Jun · 15 Sep · 15 Dec · 15 Mar",
   {"type": "dates", "dates": ["06-15", "09-15", "12-15", "03-15"]}, "M", ALWAYS,
   ["Estimated income"], ["Challan"], "maker:accounts", src="https://www.incometax.gov.in")
ob("IN.IT.ITR", "Income-tax return & tax audit report", "tax", "Income-tax Act, 2025",
   "Income Tax Dept", "IN", "annual", "Audit report 30 Sep; return 31 Oct (audit cases)",
   {"type": "annual", "month": 10, "day": 31}, "H", ALWAYS, ["Audited financials"],
   ["ITR acknowledgement", "Audit report acknowledgement"], "maker:accounts", wf="high_risk",
   src="https://www.incometax.gov.in", verify=True)
ob("IN.MCA.AGM", "Annual General Meeting", "corporate", "Companies Act, 2013 s.96", "ROC", "IN",
   "annual", "Within 6 months of FY end (30 Sep)", {"type": "annual", "month": 9, "day": 30}, "M",
   COMPANY, ["Audited accounts, notice, board report"], ["Notice, minutes"], "maker:cs",
   ai=["board_report_draft"], src="https://www.mca.gov.in")
ob("IN.MCA.AOC4", "AOC-4 financial statements filing", "corporate", "Companies Act, 2013 s.137",
   "ROC", "IN", "annual", "Within 30 days of AGM", {"type": "annual", "month": 10, "day": 30}, "H",
   COMPANY, ["Audited financials, AGM date"], ["SRN / challan"], "maker:cs",
   src="https://www.mca.gov.in", penalty="Additional fee ₹100/day")
ob("IN.MCA.MGT7", "MGT-7 / MGT-7A annual return", "corporate", "Companies Act, 2013 s.92", "ROC",
   "IN", "annual", "Within 60 days of AGM", {"type": "annual", "month": 11, "day": 29}, "H",
   COMPANY, ["Shareholding, directors, meetings"], ["SRN / challan"], "maker:cs",
   src="https://www.mca.gov.in", penalty="Additional fee ₹100/day")
ob("IN.MCA.DPT3", "DPT-3 return of deposits", "corporate", "Companies (Acceptance of Deposits) Rules",
   "ROC", "IN", "annual", "30 June", {"type": "annual", "month": 6, "day": 30}, "L", COMPANY,
   ["Loans/advances outstanding as on 31 Mar"], ["SRN"], "maker:cs", src="https://www.mca.gov.in")
ob("IN.MCA.MSME1", "MSME-1 half-yearly return (dues to MSEs > 45 days)", "corporate",
   "Companies Act s.405 order", "ROC", "IN", "half_yearly", "30 Apr · 31 Oct",
   {"type": "dates", "dates": ["04-30", "10-31"]}, "M",
   ALL(COMPANY, F("owes_mse_suppliers", "eq")), ["Ageing of MSE payables"], ["SRN"], "maker:cs",
   src="https://www.mca.gov.in", verify=True)
ob("IN.MCA.KYC", "Director KYC (DIR-3 KYC)", "corporate", "Companies (Appointment of Directors) Rules",
   "ROC", "IN", "annual", "30 Sep (check current periodicity)",
   {"type": "annual", "month": 9, "day": 30}, "L",
   F("legal_form", "in", ["pvt_ltd", "public_ltd", "llp"]), ["Director KYC"], ["SRN"],
   "maker:cs", src="https://www.mca.gov.in", verify=True)
ob("IN.LLP.8_11", "LLP Form 11 (30 May) & Form 8 (30 Oct)", "corporate", "LLP Act, 2008", "ROC",
   "IN", "annual", "Form 11 by 30 May; Form 8 by 30 Oct", {"type": "dates", "dates": ["05-30", "10-30"]},
   "M", F("legal_form", "eq", "llp"), ["Partners, contribution, accounts"], ["SRN"], "maker:cs",
   src="https://www.mca.gov.in")
ob("IN.MSMED.45", "Pay Micro/Small suppliers within 45 days", "tax",
   "MSMED Act, 2006 s.15; Income-tax disallowance for delayed MSE payments", "—", "IN", "monthly",
   "Monthly ageing review", {"type": "month_end"}, "M", F("owes_mse_suppliers", "eq"),
   ["Payables ageing with supplier Udyam status"], ["Ageing report reviewed"], "maker:accounts",
   ai=["mse_ageing_note"], verify=True)
# ---- Environment
ob("IN.ENV.CTO", "Consent to Operate (Water & Air Acts) — renewal", "environment",
   "Water Act 1974 s.25; Air Act 1981 s.21", "State PCB (MPCB in MH)", "IN", "renewal",
   "Apply well before expiry (lead time 120 days)",
   {"type": "before_expiry", "licence": "cto", "days": 120}, "H",
   F("pcb_category", "in", ["red", "orange", "green"]),
   ["Production/capacity, water consumption, effluent & emission data", "Compliance with existing conditions"],
   ["CTO copy", "Renewal application"], "maker:ehs", wf="high_risk", ai=["cto_conditions"],
   src="https://mpcb.gov.in", penalty="Closure directions; prosecution",
   audit="Walk CTO conditions one by one with evidence")
ob("IN.ENV.FORMV", "Environmental Statement (Form V)", "environment",
   "Environment (Protection) Rules, 1986 r.14", "State PCB", "IN", "annual", "30 September",
   {"type": "annual", "month": 9, "day": 30}, "M", F("pcb_category", "in", ["red", "orange", "green"]),
   ["Water, raw-material, waste and emission data for the FY"], ["Form V acknowledgement"],
   "maker:ehs", ai=["form_v_draft"], src="https://mpcb.gov.in")
ob("IN.ENV.MON", "Stack / effluent / ambient monitoring by recognised lab", "environment",
   "CTO conditions", "State PCB", "IN", "monthly", "As per CTO (typically monthly/quarterly)",
   {"type": "monthly_day", "day": 28}, "M",
   ALL(SEC("manufacturing"), F("pcb_category", "in", ["red", "orange"])),
   ["Lab reports"], ["NABL/MoEF lab report"], "maker:ehs", verify=True)
ob("IN.ENV.HW", "Hazardous waste: authorisation, 90-day storage, manifests, annual return (Form 4)",
   "environment", "Hazardous and Other Wastes (M&TM) Rules, 2016", "State PCB", "IN", "annual",
   "Annual return by 30 June; manifest per consignment", {"type": "annual", "month": 6, "day": 30},
   "H", F("hazardous_waste", "eq"), ["Waste generated/stored/disposed by category", "Manifests"],
   ["Form 4 acknowledgement", "TSDF manifests", "Authorisation"], "maker:ehs",
   ai=["hw_form4"], src="https://mpcb.gov.in")
ob("IN.ENV.EPR", "Plastic packaging EPR (PIBO): registration & annual return", "environment",
   "Plastic Waste Management Rules, 2016 (as amended)", "CPCB", "IN", "annual", "30 June (verify)",
   {"type": "annual", "month": 6, "day": 30}, "M", F("plastic_packaging", "eq"),
   ["Plastic packaging introduced by category"], ["EPR portal return"], "maker:ehs",
   src="https://eprplastic.cpcb.gov.in", verify=True)
ob("IN.ENV.EWASTE", "E-waste: channelise to registered recyclers; keep records", "environment",
   "E-Waste (Management) Rules, 2022", "CPCB / State PCB", "IN", "annual", "Records; return if required (verify)",
   {"type": "annual", "month": 6, "day": 30}, "L", F("ewaste_bulk", "eq"),
   ["E-waste disposed, recycler details"], ["Recycler receipts"], "maker:ehs", verify=True)
ob("IN.ENV.DG", "DG set emission & noise compliance", "environment",
   "Environment (Protection) Rules — DG set norms; CTO", "State PCB", "IN", "quarterly",
   "Quarterly monitoring (verify against CTO)", {"type": "dates", "dates": ["03-31", "06-30", "09-30", "12-31"]},
   "L", F("dg_set_kva", "gt", 0), ["Running hours, stack test"], ["Monitoring report"], "maker:ehs",
   verify=True)
# ---- Fire, building, lifts
ob("MH.FIRE.FORMB", "Fire: Form B (half-yearly certificate by licensed agency)", "fire_safety",
   "Maharashtra Fire Prevention and Life Safety Measures Act, 2006", "Maharashtra Fire Services",
   "IN-MH", "half_yearly", "January and July", {"type": "dates", "dates": ["01-31", "07-31"]}, "H",
   ALL(MH, F("fire_noc_required", "eq")), ["Agency inspection report", "Fire system maintenance log"],
   ["Form B submitted", "Agency licence copy"], "maker:ehs", src="https://mahafireservice.gov.in",
   penalty="Sealing of premises; prosecution")
ob("IN.FIRE.DRILL", "Fire & evacuation drills; fire-fighting training", "fire_safety",
   "National Building Code 2016 Part 4; state fire rules", "Fire Services", "IN", "half_yearly",
   "Twice a year", {"type": "dates", "dates": ["03-31", "09-30"]}, "M", F("fire_noc_required", "eq"),
   ["Drill plan, participants"], ["Drill report, attendance, photos"], "site_user", wf="fast",
   ai=["drill_report"])
ob("MH.LIFT", "Lift licence / periodic inspection", "fire_safety",
   "Maharashtra Lifts, Escalators and Moving Walks Act, 2017", "Lift Inspector (PWD/Energy Dept)",
   "IN-MH", "annual", "Annual (verify)", {"type": "before_expiry", "licence": "lift_licence", "days": 45},
   "M", ALL(MH, F("has_lift", "eq")), ["AMC report"], ["Licence / inspection certificate"],
   "maker:ehs", verify=True)
# ---- Electrical
ob("IN.ELEC.INSP", "Electrical installation: periodic inspection / self-certification", "electrical",
   "CEA (Measures relating to Safety and Electric Supply) Regulations, 2023", "Electrical Inspector",
   "IN", "renewal", "Periodic (as notified; ≤ 5 years)", {"type": "before_expiry", "licence": "elec_inspection", "days": 60},
   "H", F("ht_installation", "eq"), ["Single-line diagram, test reports"],
   ["Inspection / self-certification report"], "maker:ehs", wf="high_risk",
   src="https://cea.nic.in", verify=True)
ob("IN.ELEC.EARTH", "Earthing, IR & protection tests with records", "electrical",
   "CEA Safety Regulations, 2023", "Electrical Inspector", "IN", "annual", "Annual",
   {"type": "annual", "month": 4, "day": 30}, "M",
   ANY(F("uses_power", "eq"), F("ht_installation", "eq"), SEC("electrical")),
   ["Test readings by licensed electrical contractor"], ["Test certificate"], "maker:ehs")
ob("IN.ELEC.ACC", "Report electrical accident to Electrical Inspector", "electrical",
   "Electricity Act 2003 s.161; CEA regulations", "Electrical Inspector", "IN", "event",
   "Within 24 hours (verify form)", {"type": "event_within", "event": "electrical_accident", "days": 1},
   "H", ANY(F("uses_power", "eq"), F("ht_installation", "eq"), SEC("electrical")),
   ["Incident details"], ["Intimation copy"], "maker:ehs", wf="event", ai=["incident_intimation"],
   verify=True)
ob("MH.ELEC.CONLIC", "Electrical contractor licence renewal", "electrical",
   "Maharashtra electrical licensing regulations (Licensing Board)", "Electrical Licensing Board", "IN-MH",
   "renewal", "Before expiry", {"type": "before_expiry", "licence": "elec_contractor_licence", "days": 60},
   "H", ALL(MH, F("electrical_contractor", "eq")), ["Supervisor & wireman certificates"],
   ["Renewed licence"], "maker:admin", verify=True)
ob("IN.ELEC.COMP", "Supervisor / wireman competency certificates valid on every job",
   "electrical", "CEA Safety Regulations, 2023", "Electrical Inspector", "IN", "monthly",
   "Monthly check", {"type": "month_end"}, "M", F("electrical_contractor", "eq"),
   ["Deployment roster, certificate validity"], ["Roster with certificate numbers"], "maker:admin")
# ---- Boilers, pressure plant, lifting
ob("IN.BOILER", "Boiler certificate renewal (annual inspection)", "boiler_pv",
   "Boilers Act, 2025 (in force 1-May-2025)", "Chief Inspector of Boilers", "IN", "renewal",
   "Before certificate expiry", {"type": "before_expiry", "licence": "boiler_cert", "days": 45}, "H",
   F("has_boiler", "eq"), ["Boiler log, water treatment log", "Attendant competency"],
   ["Certificate to operate"], "maker:ehs", wf="high_risk", src="https://dpiit.gov.in",
   verify=True, penalty="Operating without valid certificate — penalty/prosecution")
ob("IN.PV.TEST", "Pressure vessels / air receivers — periodic examination", "boiler_pv",
   "OSH Code state rules; SMPV(U) Rules 2016 where applicable", "Competent person / PESO", "IN",
   "annual", "Per rules (verify periodicity)", {"type": "annual", "month": 8, "day": 31}, "M",
   F("has_pressure_vessel", "eq"), ["Equipment list, last test date"], ["Competent person certificate"],
   "maker:ehs", verify=True)
ob("IN.LIFTING", "Lifting machines & tackles — examination by competent person", "boiler_pv",
   "OSH Code state rules", "Competent person", "IN", "annual", "Every 12 months (verify)",
   {"type": "annual", "month": 8, "day": 31}, "M", F("has_lifting", "eq"),
   ["Register of lifting equipment"], ["Examination certificate"], "maker:ehs", verify=True)
# ---- Legal metrology
ob("MH.LM.VERIFY", "Weighing & measuring instruments — verification & stamping", "metrology",
   "Legal Metrology Act 2009; state enforcement rules", "Legal Metrology Dept", "IN-MH", "annual",
   "Every 12 months (most instruments)", {"type": "before_expiry", "licence": "lm_stamp", "days": 30},
   "M", F("weighing_instruments", "eq"), ["Instrument list"], ["Verification certificate"],
   "maker:admin", verify=True)
ob("IN.LM.PKG", "Packaged commodities: registration & label declarations", "metrology",
   "Legal Metrology (Packaged Commodities) Rules, 2011", "Legal Metrology Dept", "IN", "one_time",
   "Before packing/selling", {"type": "one_time"}, "M", F("packaged_goods", "eq"),
   ["SKU labels"], ["Registration certificate", "Label review"], "maker:admin",
   ai=["label_check"])
# ---- Healthcare (MH + central)
ob("MH.HC.NHREG", "Nursing home registration — renewal", "healthcare",
   "Maharashtra Nursing Homes Registration Act, 1949 (as amended) & rules", "Local supervising authority",
   "IN-MH", "renewal", "Before expiry (verify validity)",
   {"type": "before_expiry", "licence": "nh_registration", "days": 90}, "H",
   ALL(MH, SEC("healthcare"), F("beds", "gt", 0)), ["Beds, staff, facilities"],
   ["Registration certificate"], "maker:admin", wf="high_risk", verify=True)
ob("MH.HC.RATES", "Display of rates & patient rights charter", "healthcare",
   "Maharashtra Nursing Homes rules (as amended) / Clinical Establishments standards", "Supervising authority",
   "IN-MH", "continuous", "Maintain", {"type": "monthly_selfcheck"}, "L", ALL(MH, SEC("healthcare")),
   ["Current tariff"], ["Photo of display (dated)"], "site_user", wf="fast",
   ai=["patient_rights_charter"], verify=True)
ob("IN.HC.BMW.AUTH", "Bio-medical waste authorisation", "healthcare",
   "Bio-Medical Waste Management Rules, 2016", "State PCB", "IN", "renewal", "Before expiry",
   {"type": "before_expiry", "licence": "bmw_auth", "days": 90}, "H", SEC("healthcare"),
   ["Beds, waste quantities, CBWTF agreement"], ["Authorisation"], "maker:ehs", wf="high_risk",
   src="https://mpcb.gov.in")
ob("IN.HC.BMW.AR", "BMW annual report (Form IV)", "healthcare", "BMW Rules, 2016 r.13",
   "State PCB", "IN", "annual", "30 June", {"type": "annual", "month": 6, "day": 30}, "H",
   SEC("healthcare"), ["Category-wise waste (yellow/red/white/blue) for calendar year", "Training records"],
   ["Form IV acknowledgement"], "maker:ehs", ai=["bmw_form_iv"], src="https://mpcb.gov.in")
ob("IN.HC.BMW.WEB", "BMW monthly record on website; daily register; bar-coded bags", "healthcare",
   "BMW Rules, 2016 (as amended 2018)", "State PCB", "IN", "monthly", "Monthly website update",
   {"type": "monthly_day", "day": 10}, "M", ALL(SEC("healthcare"), F("beds", "gt", 0)),
   ["CBWTF manifests", "Daily weights"], ["Website screenshot", "Register extract"], "maker:ehs",
   verify=True)
ob("IN.HC.BMW.TRAIN", "BMW training & staff immunisation", "healthcare", "BMW Rules, 2016 r.4",
   "State PCB", "IN", "annual", "Annual training", {"type": "annual", "month": 12, "day": 31}, "M",
   SEC("healthcare"), ["Staff list"], ["Training attendance", "Immunisation records"], "maker:hr",
   ai=["training_module"])
ob("IN.HC.PNDT.MR", "PC-PNDT monthly report & Form F completeness", "healthcare",
   "PC & PNDT Act, 1994 and Rules", "Appropriate Authority", "IN", "monthly",
   "By 5th of following month", {"type": "monthly_day", "day": 5}, "H", F("ultrasound_units", "gt", 0),
   ["Form F for every USG (online)", "Machine register"], ["Monthly report acknowledgement"],
   "maker:clinical", wf="high_risk", penalty="Imprisonment, fine, sealing of machine",
   audit="Sample Form F: 100% fields complete, declarations signed")
ob("IN.HC.PNDT.REG", "PC-PNDT registration renewal", "healthcare", "PC & PNDT Rules", "Appropriate Authority",
   "IN", "renewal", "Every 5 years, 30 days before expiry",
   {"type": "before_expiry", "licence": "pndt_reg", "days": 30}, "H", F("ultrasound_units", "gt", 0),
   ["Machines, qualified operators"], ["Renewed registration"], "maker:clinical", wf="high_risk")
ob("IN.HC.AERB.LIC", "AERB licence (eLORA) for X-ray/CT — renewal", "healthcare",
   "Atomic Energy (Radiation Protection) Rules, 2004", "AERB", "IN", "renewal", "Before expiry",
   {"type": "before_expiry", "licence": "aerb_licence", "days": 90}, "H", F("xray_units", "gt", 0),
   ["Equipment, QA reports, RSO"], ["eLORA licence"], "maker:clinical", wf="high_risk",
   src="https://elora.aerb.gov.in")
ob("IN.HC.AERB.TLD", "Personnel radiation monitoring (TLD) & QA tests", "healthcare",
   "AERB safety code / RP Rules", "AERB", "IN", "quarterly", "Quarterly TLD; QA as prescribed",
   {"type": "dates", "dates": ["03-31", "06-30", "09-30", "12-31"]}, "M", F("xray_units", "gt", 0),
   ["Radiation workers list"], ["TLD dose reports", "QA certificate"], "maker:clinical", verify=True)
ob("IN.HC.DRUG", "Drug licence (retail) — validity, pharmacist, Schedule H1 register", "healthcare",
   "Drugs and Cosmetics Act, 1940 & Rules", "FDA (State)", "IN", "renewal", "Retention before due",
   {"type": "before_expiry", "licence": "drug_licence", "days": 90}, "H", F("pharmacy", "eq"),
   ["Registered pharmacist details", "H1 register"], ["Licence, retention fee challan"],
   "maker:pharmacy", wf="high_risk", verify=True)
ob("IN.HC.NDPS", "NDPS: recognised medical institution, stock registers", "healthcare",
   "NDPS Act, 1985 & rules (essential narcotic drugs)", "State Drugs Controller", "IN", "monthly",
   "Monthly stock reconciliation (verify returns)", {"type": "month_end"}, "H", F("ndps_stock", "eq"),
   ["Receipts, issues, balance"], ["Signed stock register extract"], "maker:pharmacy", wf="high_risk",
   verify=True)
ob("IN.HC.BLOOD", "Blood centre licence — renewal", "healthcare", "Drugs and Cosmetics Rules (blood centres)",
   "CDSCO / State FDA", "IN", "renewal", "Before expiry",
   {"type": "before_expiry", "licence": "blood_licence", "days": 90}, "H", F("blood_centre", "eq"),
   ["Licence, staff"], ["Renewed licence"], "maker:clinical", wf="high_risk")
ob("IN.HC.CALIB", "Biomedical equipment calibration & preventive maintenance", "healthcare",
   "Quality standards (NABH) / manufacturer requirements", "Internal / NABH", "IN", "annual",
   "Per asset schedule", {"type": "annual", "month": 3, "day": 31}, "M", SEC("healthcare"),
   ["Asset register with calibration due dates"], ["Calibration certificates"], "maker:biomed")
# ---- Construction
ob("IN.CON.EREG", "Registration of establishment for building / construction work", "construction",
   "OSH Code, 2020 (building or other construction work)", "Registering Officer", "IN", "one_time",
   "Before commencement of work", {"type": "one_time"}, "H",
   ALL(SEC("construction"), F("construction_active", "eq"), F("construction_workers", "gte", 10)),
   ["Project, location, cost, workers, duration"], ["Registration certificate"], "maker:pm",
   wf="high_risk", verify=True)
ob("IN.CON.CESS", "Building & other construction workers cess (1% of cost)", "construction",
   "Code on Social Security, 2020 (BOCW cess)", "Cess assessing officer / welfare board", "IN",
   "event", "As per self-assessment & payment schedule (verify)",
   {"type": "event_within", "event": "construction_milestone", "days": 30}, "H",
   ALL(SEC("construction"), F("construction_active", "eq")), ["Cost of construction to date"],
   ["Cess payment receipt", "Self-assessment"], "maker:accounts", ai=["cess_working"], verify=True,
   penalty="Interest and penalty on unpaid cess")
ob("IN.CON.SAFETY", "Site safety: daily checklist, scaffolding/lifting inspection, PPE, welfare",
   "construction", "OSH Code, 2020 + building work rules; NBC Part 7", "Inspector-cum-Facilitator", "IN",
   "continuous", "Daily / weekly checklists", {"type": "monthly_selfcheck"}, "H",
   ALL(SEC("construction"), F("construction_active", "eq")), ["Checklist responses, photos"],
   ["Signed checklists, photos"], "site_user", wf="fast", ai=["toolbox_talk"])
ob("MH.RERA.QPR", "MahaRERA quarterly project progress update", "construction",
   "RERA 2016 s.11; MahaRERA regulations", "MahaRERA", "IN-MH", "quarterly",
   "Within 7 days of quarter end (verify)", {"type": "dates", "dates": ["01-07", "04-07", "07-07", "10-07"]},
   "H", ALL(MH, F("rera_project", "eq")), ["Units booked, construction status, approvals"],
   ["Portal update screenshot"], "maker:pm", src="https://maharera.maharashtra.gov.in", verify=True)
ob("MH.RERA.FORM5", "RERA annual audited statement of project account (Form 5)", "construction",
   "RERA 2016 s.4(2)(l)(D)", "MahaRERA", "IN-MH", "annual", "Within 6 months of FY end (verify)",
   {"type": "annual", "month": 9, "day": 30}, "H", ALL(MH, F("rera_project", "eq")),
   ["Project account statement, CA certificate"], ["Form 5 upload"], "maker:accounts",
   src="https://maharera.maharashtra.gov.in", verify=True)
# ---- Data protection
ob("IN.DPDP.PROG", "DPDP: notices, consent, rights, retention, breach response (full compliance by 13-May-2027)",
   "data_protection", "Digital Personal Data Protection Act, 2023 & DPDP Rules, 2025",
   "Data Protection Board of India", "IN", "one_time", "Programme milestones to 13 May 2027",
   {"type": "fixed", "date": "2027-05-13"}, "M", ALWAYS,
   ["Personal data inventory (employees, patients, customers)", "Processors list"],
   ["Privacy notice", "Retention schedule", "Breach runbook", "Processor DPAs"], "maker:admin",
   ai=["privacy_notice", "retention_schedule"], src="https://www.meity.gov.in",
   penalty="Penalties up to ₹250 crore per breach category")
ob("IN.DPDP.BREACH", "Personal data breach intimation to Board & affected persons", "data_protection",
   "DPDP Rules, 2025", "Data Protection Board of India", "IN", "event",
   "Without delay; detailed report within prescribed time (verify)",
   {"type": "event_within", "event": "data_breach", "days": 3}, "H", ALWAYS,
   ["Breach facts, data affected, mitigation"], ["Intimation copies"], "maker:admin", wf="event",
   ai=["breach_intimation"], verify=True)

# ------------------------------------------------------------------- licence types (renewals)
LICENCES = {
    "factory_licence": "Factory licence", "cto": "Consent to Operate", "lift_licence": "Lift licence",
    "elec_inspection": "Electrical inspection", "elec_contractor_licence": "Electrical contractor licence",
    "boiler_cert": "Boiler certificate", "lm_stamp": "Legal metrology stamping",
    "nh_registration": "Nursing home registration", "bmw_auth": "BMW authorisation",
    "pndt_reg": "PC-PNDT registration", "aerb_licence": "AERB licence", "drug_licence": "Drug licence",
    "blood_licence": "Blood centre licence",
}

CATEGORIES = {
    "labour": "Labour", "social_security": "Social security", "tax": "Tax", "corporate": "Corporate",
    "environment": "Environment", "fire_safety": "Fire & building", "electrical": "Electrical",
    "boiler_pv": "Boilers & pressure plant", "metrology": "Legal metrology",
    "healthcare": "Healthcare", "construction": "Construction", "posh": "POSH",
    "data_protection": "Data protection",
}


def rule_text(r) -> str:
    if "all" in r:
        return "always" if not r["all"] else " AND ".join(rule_text(x) for x in r["all"])
    if "any" in r:
        return "(" + " OR ".join(rule_text(x) for x in r["any"]) + ")"
    sym = {"eq": "=", "gte": "≥", "gt": ">", "lte": "≤", "in": "in", "contains": "includes",
           "not_contains": "excludes"}[r["op"]]
    v = r["value"]
    if r["op"] == "eq" and v is True:
        return r["fact"]
    if r["op"] == "eq" and v is False:
        return f"not {r['fact']}"
    return f"{r['fact']} {sym} {'/'.join(v) if isinstance(v, list) else v}"


def main() -> None:
    out = {"version": "0.1.0", "generated_by": "content/seed/build_seed.py",
           "status": "draft — every item pending SME review; verify=true items need a fact check",
           "facts": FACTS, "categories": CATEGORIES, "licence_types": LICENCES, "obligations": O}
    (ROOT / "content/seed/obligations.seed.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    rows = ["| ID | Obligation | Law | Freq | Due | Risk | Applies when | ✓ |", "|---|---|---|---|---|---|---|---|"]
    for o in O:
        rows.append(f"| `{o['id']}` | {o['title']} | {o['law']} | {o['frequency']} | {o['due']} | "
                    f"{o['risk']} | {rule_text(o['applies'])} | {'verify' if o['verify'] else ''} |")
    doc = ROOT / "docs/COMPLIANCE_UNIVERSE.md"
    text = doc.read_text(encoding="utf-8")
    start, end = "<!-- REGISTER:START -->", "<!-- REGISTER:END -->"
    a, b = text.index(start) + len(start), text.index(end)
    doc.write_text(text[:a] + "\n" + "\n".join(rows) + "\n" + text[b:], encoding="utf-8")
    print(f"{len(O)} obligations; {sum(o['verify'] for o in O)} flagged verify")


if __name__ == "__main__":
    main()
