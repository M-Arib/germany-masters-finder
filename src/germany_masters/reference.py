"""Hand-curated reference data that DAAD does not provide.

Every entry here was checked on an official or cited source in October 2026.
Deadlines and fees change every year: re-check the sources before each intake.
"""

# --- Application opening dates -------------------------------------------------
# DAAD often lists only the deadline ("until 30 November"), never when the portal
# opens. Used only when DAAD gives no start date. "program" = None applies to all
# programmes of that university.
KNOWN_APPLICATION_OPENINGS = [
    {"university": "Technical University of Munich", "program": None,
     "start": "1 October 2026", "deadline": "30 November 2026",
     "source": "https://www.cit.tum.de/en/cit/studies/degree-programs/master-informatics/",
     "note": "TUM CIT summer window 1 Oct - 30 Nov (verified on the Informatics page)"},
    {"university": "RWTH Aachen University", "program": "Data Science",
     "start": "June 2026 (approx.)", "deadline": "1 September 2026",
     "source": "https://sc.informatik.rwth-aachen.de/de/?p=14325",
     "note": "Non-EU: June to 1 September; central RWTH page takes precedence"},
    {"university": "University of Bonn", "program": None,
     "start": "1 October 2026", "deadline": "1 November 2026",
     "source": "https://www.informatik.uni-bonn.de/en/studies/examination-office/deadlines-at-a-glance",
     "note": "2nd period (EEA applicants only): 15 Dec 2026 - 15 Jan 2027"},
    {"university": "University of Göttingen", "program": "Applied Computer Science",
     "start": "Mid-September 2026 (approx.)", "deadline": "15 October 2026",
     "source": "https://www.uni-goettingen.de/en/619514.html",
     "note": "Portal opens ~1 month before the deadline. EU/EEA deadline: 15 Dec 2026"},
    {"university": "University of Tübingen", "program": "Bioinformatics",
     "start": "1 December 2026", "deadline": "15 January 2027",
     "source": "https://uni-tuebingen.de/en/74459",
     "note": "Non-EU deadline 15 Jan; EU/German deadline 15 Mar"},
    {"university": "Technical University of Darmstadt", "program": "Artificial Intelligence",
     "start": "1 December 2026", "deadline": "15 January 2027",
     "source": "https://www.informatik.tu-darmstadt.de/studium_fb20/im_studium/studiengaenge_liste/aim_msc.en.jsp",
     "note": "Summer term: 01.12. - 15.01."},
    {"university": "University of Münster", "program": None,
     "start": "Late September 2026", "deadline": "30 November 2026",
     "source": "https://master-geoinformatics.com/apply",
     "note": "Non-EU deadline 30 Nov; EU deadline 15 Jan"},
    {"university": "Leibniz University Hannover", "program": None,
     "start": "15 October 2026", "deadline": "30 November 2026",
     "source": "https://www.myguide.de/en/international-programmes-master/detail/"
               "leibniz-university-hannover-computer-science-master-of-science-8935/?ip-id=8935",
     "note": "Non-EU: 15 Oct - 30 Nov (needs uni-assist VPD first, up to 8 weeks). EU: 1 Dec - 15 Jan"},
    {"university": "University of Bayreuth", "program": None,
     "start": "15 October 2026", "deadline": "15 January 2027",
     "source": "https://www.uni-bayreuth.de/en/master/computer-science",
     "note": "Non-EU: 15 Oct - 15 Jan. EU/German: 15 Oct - 15 Apr"},
    {"university": "University of Augsburg", "program": "Data Science",
     "start": "Mid-September 2026", "deadline": "1 March 2027",
     "source": "https://www.uni-augsburg.de/en/fakultaet/fai/informatik/studienangebot/msc-dsc/",
     "note": "Visa applicants advised to apply by 1 November"},
    {"university": "University of Siegen", "program": "Quantum Science",
     "start": "1 August 2026", "deadline": "31 October 2026",
     "source": "https://www.uni-siegen.de/en/study/master/quantum-science",
     "note": "Non-EU school-leaving cert: 1 Aug - 31 Oct. Others: 1 Oct - 30 Mar"},
    {"university": "Technische Universität Ilmenau", "program": None,
     "start": "1 August 2026", "deadline": "15 November 2026",
     "source": "https://www.tu-ilmenau.de/en/study/in-study/course-of-studies/administrative-guide/"
               "deadlines-and-dates/application-periods",
     "note": "Non-EU (third-country) master's applicants"},
    {"university": "Marburg University", "program": None,
     "start": "1 October 2026", "deadline": "15 January 2027",
     "source": "https://www.uni-marburg.de/en/studying/after-your-first-degree/masters-programs/"
               "application-for-a-masters-programme/master-application-deadlines",
     "note": "Via uni-assist (allow 4-6 weeks processing)"},
    {"university": "Heilbronn University of Applied Sciences", "program": None,
     "start": "Mid-November 2026", "deadline": None,
     "source": "https://www.hs-heilbronn.de/en/master-application",
     "note": "Portals open mid-November for the summer semester"},
    {"university": "SRH University", "program": None,
     "start": "Rolling (open all year)", "deadline": "Until places are filled",
     "source": "https://www.mygermanuniversity.com/universities/SRH-University/application-deadlines",
     "note": "No fixed deadline; apply early (third-party source, confirm with SRH)"},
    {"university": "RheinMain University of Applied Sciences", "program": None,
     "start": "Early December 2026 (expected)", "deadline": "15 January 2027",
     "source": "https://www.hs-rm.de/en/studying-with-us/application-and-enrollment/international-applicants",
     "note": "uni-assist opened early Dec 2025 for summer 2026; 2027 not yet confirmed"},
    {"university": "Stuttgart Technical University of Applied Sciences", "program": "Software Technology",
     "start": "5 May 2026 (regular phase, closed)", "deadline": "31 August 2026",
     "source": "https://www.hft-stuttgart.de/informatik/master-software-technology",
     "note": "Extra phase 5 Nov - 15 Jan ONLY if places remain"},
    {"university": "Fulda University of Applied Sciences", "program": None,
     "start": "1 November 2026", "deadline": "1 December 2026",
     "source": "https://www.hs-fulda.de/en/studyprogramme/global-software-development-msc",
     "note": "Non-EU with foreign degree. German degree / EU: until 31 March"},
    {"university": "Furtwangen University", "program": "Business Consulting",
     "start": "15 April 2026", "deadline": "15 October 2026",
     "source": "https://www.hs-furtwangen.de/en/programmes/business-consulting-master/",
     "note": "Application period 15 April - 15 October"},
    {"university": "OWL University of Applied Sciences", "program": None,
     "start": "17 November 2026", "deadline": "15 January 2027",
     "source": "https://www.th-owl.de/en/studies/available-courses/degree-programs/detail/information-technology/",
     "note": "International applicants: 17.11. - 15.01."},
]

# --- QS World University Rankings 2026 ------------------------------------------
# Source: https://www.learngermanonline.org/top-german-universities/ (checked Oct 2026),
# consistent with hotcoursesabroad.com and iamexpat.de. Missing = not in the QS 2026 table.
QS_2026 = {
    "Technical University of Munich": "22",
    "RWTH Aachen University": "105",
    "University of Freiburg": "201",
    "University of Bonn": "207",
    "University of Tübingen": "215",
    "Dresden University of Technology": "218",
    "TUD Dresden University of Technology": "218",
    "University of Göttingen": "243",
    "Technical University of Darmstadt": "253",
    "University of Stuttgart": "310",
    "University of Münster": "350",
    "Julius-Maximilians-Universität Würzburg": "416",
    "Leibniz University Hannover": "433",
    "University of Konstanz": "440",
    "University of Bayreuth": "448",
    "University of Potsdam": "477",
    "Ulm University": "546",
    "Kiel University": "618",
    "Saarland University": "635",
    "TU Dortmund University": "673",
    "University of Regensburg": "691",
    "Technische Universität Braunschweig": "711-720",
    "Marburg University": "771-780",
    "University of Rostock": "851-900",
    "RPTU University Kaiserslautern-Landau": "1201-1400",
    "University of Siegen": "1201-1400",
}

# Universities of applied sciences whose English name doesn't say so
APPLIED_SCIENCES_NAMES = {
    "Aalen University",
    "Albstadt-Sigmaringen University",
    "Deggendorf Institute of Technology",
    "Furtwangen University",
}

# --- One-line context per university (well-established facts only) --------------
UNI_FACTS = {
    "Technical University of Munich": "Germany's highest-ranked university (QS #22), home to the Munich Institute "
                                      "of Robotics and Machine Intelligence (MIRMI)",
    "RWTH Aachen University": "Germany's flagship engineering university with deep industry and automation ties",
    "University of Bonn": "home of the Lamarr Institute for Machine Learning and AI, one of Germany's "
                          "national AI centres",
    "TU Dortmund University": "co-host of the Lamarr Institute for Machine Learning and AI, one of Germany's "
                              "national AI centres",
    "University of Tübingen": "part of Cyber Valley and the Tübingen AI Center, among Europe's strongest "
                              "machine-learning clusters",
    "University of Stuttgart": "part of Cyber Valley, one of Europe's largest AI research consortia, next to "
                               "a major automotive industry",
    "Technical University of Darmstadt": "a founding member of hessian.AI, the state AI centre of Hesse",
    "University of Freiburg": "a leading research university (QS #201) with well-known robotics and "
                              "machine-learning groups",
    "Saarland University": "on the same campus as DFKI and two Max Planck Institutes for computer science",
    "University of Göttingen": "a top-250 research university with a strong data-science and "
                               "scientific-computing ecosystem",
    "Leibniz University Hannover": "home of the L3S Research Center for AI and web science",
    "RPTU University Kaiserslautern-Landau": "located next to a DFKI site, Germany's largest AI research institute",
    "University of Potsdam": "closely linked to the Hasso Plattner Institute for digital engineering",
    "Paderborn University": "home of the Heinz Nixdorf Institute for intelligent technical systems",
    "Osnabrück University": "home of one of Germany's first and best-known Cognitive Science institutes",
    "Julius-Maximilians-Universität Würzburg": "home of the CAIDAS centre for AI and data science",
    "Dresden University of Technology": "a TU9 Excellence University and host of the ScaDS.AI centre",
    "Technische Hochschule Ingolstadt": "home of the AImotion Bavaria institute for AI in mobility",
    "Hochschule Bonn-Rhein-Sieg": "an applied-sciences university known for its autonomous-systems and "
                                  "robotics research",
    "SRH University": "a private university with a project-based block teaching model and rolling admission",
}

# --- Fees DAAD lists only as "Varied" ---------------------------------------------
FEE_OVERRIDES = {
    ("Technical University of Munich", "Informatics"):
        (6000, "TUM non-EU fee; same school as Data Engineering (€6,000). Confirm at tum.de/en/studies/fees"),
    ("University of Stuttgart", "Computer Science"):
        (1500, "Baden-Württemberg charges non-EU students €1,500 per semester"),
}

# --- uni-assist requirements found outside DAAD ----------------------------------------
UNI_ASSIST_OVERRIDES = {
    "Leibniz University Hannover": ("vpd", "Non-EU applicants need a uni-assist VPD first (processing up to 8 weeks)"),
}


def get_known_opening(university: str, program: str):
    """Returns the researched opening-date entry for a programme, or None."""
    for entry in KNOWN_APPLICATION_OPENINGS:
        if entry["university"].lower() not in (university or "").lower():
            continue
        if entry["program"] and entry["program"].lower() not in (program or "").lower():
            continue
        return entry
    return None
