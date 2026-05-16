"""Structured Annex III category data for Conforma-AI."""

from __future__ import annotations

ANNEX_III_CATEGORIES = [
    {
        "section": "1",
        "title": "Biometric identification and categorization of natural persons",
        "summary": (
            "Remote biometric identification, biometric categorization, and emotion recognition "
            "where the use is not already prohibited under Article 5."
        ),
        "paragraphs": [
            {
                "reference": "Annex III Section 1",
                "label": "Biometric identification and categorization",
                "examples": [
                    "Facial recognition for shoplifter detection in private retail settings",
                    "Biometric categorization systems used to segment people by observed traits",
                    "Emotion-recognition systems that are not prohibited outright",
                ],
            }
        ],
    },
    {
        "section": "2",
        "title": "Critical infrastructure",
        "summary": (
            "AI systems used for safety components or operational management of essential "
            "infrastructure such as road, rail, air traffic, water, gas, heating, and electricity."
        ),
        "paragraphs": [
            {
                "reference": "Annex III Section 2",
                "label": "Critical infrastructure safety and operations",
                "examples": [
                    "Road traffic safety management",
                    "Electricity or water grid control support",
                    "Rail or air traffic safety systems",
                ],
            }
        ],
    },
    {
        "section": "3",
        "title": "Education and vocational training",
        "summary": (
            "Systems affecting access to education, evaluation of learning outcomes, level "
            "placement, or monitoring prohibited behavior during tests."
        ),
        "paragraphs": [
            {
                "reference": "Annex III Section 3(a)",
                "label": "Admission and access decisions",
                "examples": ["Admissions scoring", "Selection for educational programs"],
            },
            {
                "reference": "Annex III Section 3(b)",
                "label": "Evaluation of learning outcomes",
                "examples": ["Exam grading support", "Assessment scoring for certification"],
            },
            {
                "reference": "Annex III Section 3(c)",
                "label": "Placement and level assessment",
                "examples": ["Automated class placement", "Vocational stream recommendations"],
            },
            {
                "reference": "Annex III Section 3(d)",
                "label": "Behavior monitoring during tests",
                "examples": ["Exam proctoring behavior detection", "Cheating detection"],
            },
        ],
    },
    {
        "section": "4",
        "title": "Employment, workers management, access to self-employment",
        "summary": (
            "Recruitment, worker-management, access to self-employment, promotion, termination, "
            "task allocation, and performance evaluation."
        ),
        "paragraphs": [
            {
                "reference": "Annex III Section 4(a)",
                "label": "Recruitment and access to work",
                "examples": [
                    "CV ranking",
                    "Resume scoring",
                    "Candidate filtering for hiring",
                    "Job application ranking",
                ],
            },
            {
                "reference": "Annex III Section 4(b)",
                "label": "Worker-management and employment decisions",
                "examples": [
                    "Promotion decisions",
                    "Termination support",
                    "Task allocation or productivity scoring",
                    "Performance evaluation",
                ],
            },
        ],
    },
    {
        "section": "5",
        "title": "Access to and enjoyment of essential private and public services",
        "summary": (
            "Eligibility for public benefits, creditworthiness, insurance pricing, and emergency-call "
            "evaluation where AI can materially affect essential services."
        ),
        "paragraphs": [
            {
                "reference": "Annex III Section 5(a)",
                "label": "Public assistance benefits eligibility",
                "examples": ["Benefits eligibility scoring", "Public welfare prioritization"],
            },
            {
                "reference": "Annex III Section 5(b)",
                "label": "Creditworthiness and credit scoring",
                "examples": ["Loan approval scoring", "Mortgage risk scoring"],
            },
            {
                "reference": "Annex III Section 5(c)",
                "label": "Life and health insurance pricing",
                "examples": ["Life insurance premium scoring", "Health insurance risk pricing"],
            },
            {
                "reference": "Annex III Section 5(d)",
                "label": "Emergency-call evaluation and dispatching",
                "examples": ["Emergency triage support", "Ambulance dispatch prioritization"],
            },
        ],
    },
    {
        "section": "6",
        "title": "Law enforcement",
        "summary": (
            "Risk assessment, evidence support, profiling, and similar tools used in law-enforcement "
            "workflows where decisions affect natural persons."
        ),
        "paragraphs": [
            {
                "reference": "Annex III Section 6(a)",
                "label": "Risk assessment of natural persons",
                "examples": ["Recidivism scoring", "Victim-risk screening"],
            },
            {
                "reference": "Annex III Section 6(b)",
                "label": "Polygraphs and similar tools",
                "examples": ["Automated deception analysis", "Behavioral trust scoring"],
            },
            {
                "reference": "Annex III Section 6(c)",
                "label": "Reliability of evidence",
                "examples": ["Evidence authenticity scoring", "Forensic evidence ranking"],
            },
            {
                "reference": "Annex III Section 6(d)",
                "label": "Profiling for investigations",
                "examples": ["Suspect prioritization", "Investigation targeting based on profiles"],
            },
        ],
    },
    {
        "section": "7",
        "title": "Migration, asylum, and border control management",
        "summary": (
            "Border polygraphs, migration risk assessment, and examination of visa, asylum, or "
            "residence applications."
        ),
        "paragraphs": [
            {
                "reference": "Annex III Section 7(a)",
                "label": "Polygraphs and similar tools at borders",
                "examples": ["Border deception analysis", "Behavioral screening at checkpoints"],
            },
            {
                "reference": "Annex III Section 7(b)",
                "label": "Risk assessment of natural persons crossing borders",
                "examples": ["Traveler risk scoring", "Entry-risk prioritization"],
            },
            {
                "reference": "Annex III Section 7(c)",
                "label": "Examination of asylum, visa, and residence applications",
                "examples": ["Visa application triage", "Residence permit risk assessment"],
            },
            {
                "reference": "Annex III Section 7(d)",
                "label": "Detection of irregular migration",
                "examples": ["Irregular migration pattern detection", "Border-monitoring classification"],
            },
        ],
    },
    {
        "section": "8",
        "title": "Administration of justice and democratic processes",
        "summary": (
            "Judicial support systems and AI systems capable of influencing election outcomes or voter behavior."
        ),
        "paragraphs": [
            {
                "reference": "Annex III Section 8(a)",
                "label": "Judicial decision support",
                "examples": ["Case-law research ranking", "Fact-pattern interpretation support"],
            },
            {
                "reference": "Annex III Section 8(b)",
                "label": "Democratic processes and elections",
                "examples": ["Voter influence targeting", "Election outcome manipulation support"],
            },
        ],
    },
]

ANNEX_III_OBLIGATIONS = [
    {"article": "Article 9", "obligation": "Risk management system"},
    {"article": "Article 10", "obligation": "Data and data governance"},
    {"article": "Article 11", "obligation": "Technical documentation under Annex IV"},
    {"article": "Article 12", "obligation": "Record-keeping and logging"},
    {"article": "Article 13", "obligation": "Transparency and information for deployers"},
    {"article": "Article 14", "obligation": "Human oversight"},
    {"article": "Article 15", "obligation": "Accuracy, robustness, and cybersecurity"},
    {"article": "Article 16", "obligation": "Provider obligations including CE marking"},
    {"article": "Article 26", "obligation": "Deployer obligations"},
    {"article": "Article 47-48", "obligation": "Declaration of conformity and CE marking"},
    {"article": "Article 49", "obligation": "Registration in the EU database"},
    {"article": "Article 72", "obligation": "Post-market monitoring"},
    {"article": "Article 73", "obligation": "Serious incident reporting"},
]
