"""USPTO design search code descriptions.

A design search code is six digits: a two-digit **category**, a two-digit
**division**, and a two-digit **section** (CCDDSS). The full USPTO Design Search
Code Manual enumerates ~1,500 section-level codes; we do not embed all of them.
`describe()` returns the authoritative category name plus a structural
decomposition, and a specific gloss for the handful of section codes Markery
projects rely on. Unknown sections point to the USPTO manual rather than guess.
"""

from __future__ import annotations

# Authoritative top-level categories (USPTO Design Search Code Manual).
_CATEGORIES: dict[str, str] = {
    "01": "Celestial bodies, natural phenomena, geographical maps",
    "02": "Human beings",
    "03": "Animals",
    "04": "Supernatural, fantastical or unidentifiable beings; masks",
    "05": "Plants",
    "06": "Scenery",
    "07": "Dwellings, buildings, and other structures",
    "08": "Foodstuffs",
    "09": "Textiles, clothing, sewing accessories, headwear",
    "10": "Tobacco, smokers' materials, fans, toilet articles, medical devices",
    "11": "Household utensils",
    "12": "Furniture and sanitary installations",
    "13": "Lighting, cooking, heating, and refrigeration equipment",
    "14": "Hardware, tools, and ladders",
    "15": "Machinery, motors, engines, and pumps",
    "16": "Photography, cinematography, optics, and electrical apparatus",
    "17": "Horological, measuring, and controlling instruments",
    "18": "Transport, equipment for animals, and anchors",
    "19": "Baggage, containers, and packaging",
    "20": "Stationery, office equipment, artists' and writing materials",
    "21": "Games, toys, and sporting articles",
    "22": "Musical instruments and accessories",
    "23": "Arms, ammunition, and armor",
    "24": "Heraldry, flags, crowns, emblems, symbols, insignia, and coins",
    "25": "Ornamental surfaces, frames, and decorative motifs",
    "26": "Geometric figures and solids",
    "27": "Forms of writing, numbers, punctuation, and scientific symbols",
    "28": "Inscriptions in various characters",
    "29": "Miscellaneous",
}

# Section-level glosses Markery projects depend on (high-confidence only).
_SECTIONS: dict[str, str] = {
    "030108": "Dogs of the bulldog / mastiff type",
}


def describe(code: str) -> str:
    """Return a human-readable description for a six-digit design search code."""
    code = str(code).strip()
    if len(code) != 6 or not code.isdigit():
        return f"{code} (unrecognised code format)"
    if code in _SECTIONS:
        cat = _CATEGORIES.get(code[:2], "Unknown category")
        return f"{cat} › {_SECTIONS[code]}"
    cat = _CATEGORIES.get(code[:2])
    if cat is None:
        return "Unknown category — see the USPTO Design Search Code Manual"
    return (f"{cat} › division {code[2:4]}, section {code[4:6]} "
            f"(see USPTO Design Search Code Manual for the section gloss)")
