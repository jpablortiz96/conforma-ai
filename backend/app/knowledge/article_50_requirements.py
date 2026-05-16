"""Structured Article 50 transparency requirements for Conforma-AI."""

from __future__ import annotations

ARTICLE_50_REQUIREMENTS = [
    {
        "subsection": "Article 50(1)",
        "title": "Direct interaction systems",
        "trigger": "AI systems intended to interact directly with natural persons",
        "deadline": "2 December 2026",
        "description": (
            "Natural persons must be informed in a clear and distinguishable manner that they are "
            "interacting with an AI system, unless that is obvious from context."
        ),
        "placement_guidance": "Before or at the start of the first interaction.",
        "examples": ["Customer service chatbot", "Password reset assistant", "Voice assistant"],
    },
    {
        "subsection": "Article 50(2)",
        "title": "AI-generated synthetic content",
        "trigger": "Systems generating synthetic audio, image, video, or text content",
        "deadline": "2 December 2026",
        "description": (
            "Outputs must be marked in a machine-readable format and remain detectable as "
            "artificially generated or manipulated."
        ),
        "placement_guidance": "Watermarks, metadata, or equivalent machine-readable markers.",
        "examples": ["Image generators", "Synthetic text generators", "Voice cloning tools"],
    },
    {
        "subsection": "Article 50(3)",
        "title": "Emotion recognition and biometric categorization",
        "trigger": "Deployers of emotion-recognition or biometric-categorization systems",
        "deadline": "2 December 2026",
        "description": (
            "Exposed natural persons must be informed of the operation of the system and personal "
            "data must be processed consistently with GDPR and related EU data-protection rules."
        ),
        "placement_guidance": "Pre-use notice and accessible disclosure at the point of exposure.",
        "examples": ["Emotion analytics", "Biometric categorization at a venue entrance"],
    },
    {
        "subsection": "Article 50(4)",
        "title": "Deep fakes",
        "trigger": "Deployers of AI systems that generate or manipulate deep-fake media",
        "deadline": "2 December 2026",
        "description": (
            "The deployer must disclose that the image, audio, or video has been artificially "
            "generated or manipulated."
        ),
        "placement_guidance": "Prominent overlay or equivalent conspicuous disclosure.",
        "examples": ["Consumer deep-fake video generator", "Synthetic spokesperson video"],
    },
]

ARTICLE_50_DISCLOSURE_CHARACTERISTICS = [
    "Clear and distinguishable to a reasonably well-informed, observant, and circumspect person",
    "Presented at the latest at the time of first interaction or exposure",
    "Accessible to persons with disabilities",
    "Aligned with relevant accessibility standards",
]
