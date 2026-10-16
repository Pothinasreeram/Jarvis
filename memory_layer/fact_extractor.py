import re
from datetime import datetime

from memory_layer.memory import (
    remember_entity_fact,
    remember_entity_alias,
    remember_reference
)


# ==========================================================
# HELPERS
# ==========================================================

def _clean_value(value):
    """Clean extracted text."""

    if not value:
        return None

    value = value.strip()

    value = value.rstrip(
        " .,;:"
    )

    return value


def _save(
    entity,
    fact_key,
    value,
    memory
):
    """Save a fact if the value is valid."""

    value = _clean_value(value)

    if not value:
        return

    remember_entity_fact(
        memory,
        entity,
        fact_key,
        value
    )


# ==========================================================
# FACT EXTRACTION
# ==========================================================

def extract_facts(
    entity,
    answer,
    memory=None
):
    """
    Extract useful facts from an AI answer.

    Supported facts:

        birth_date
        birth_place
        age
        net_worth
        residence
        nationality
        occupation
        companies
    """

    if not entity:
        return

    if not answer:
        return

    if memory is None:
        return

    text = answer.strip()

    if not text:
        return

    entity_name = entity.strip()


    # ======================================================
    # BIRTH DATE
    # ======================================================

    birth_date_patterns = [

        r"born on ([A-Z][a-z]+ \d{1,2}, \d{4})",

        r"born on (\d{1,2} [A-Z][a-z]+ \d{4})",

        r"born ([A-Z][a-z]+ \d{1,2}, \d{4})",

        r"born (\d{1,2} [A-Z][a-z]+ \d{4})",

    ]

    for pattern in birth_date_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            _save(
                entity_name,
                "birth_date",
                match.group(1),
                memory
            )

            break


    # ======================================================
    # BIRTHPLACE
    # ======================================================

    birth_place_patterns = [

        # Example:
        # born in Pretoria, South Africa
        r"born in ([A-Z][A-Za-z .,'-]+?)(?:\.|$)",

        # Example:
        # birthplace is Pretoria, South Africa
        r"birthplace is ([A-Z][A-Za-z .,'-]+?)(?:\.|$)",

        # Example:
        # was born in Pretoria, South Africa
        r"was born in ([A-Z][A-Za-z .,'-]+?)(?:\.|$)",

        # Example:
        # South African-born
        r"([A-Z][A-Za-z-]+)-born",

    ]

    for index, pattern in enumerate(
        birth_place_patterns
    ):

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if not match:
            continue

        place = match.group(1)

        place = _clean_value(
            place
        )

        if not place:
            continue

        # --------------------------------------------------
        # Don't treat nationality as a literal birthplace.
        #
        # "South African-born" tells us nationality/origin,
        # but not necessarily a city.
        # --------------------------------------------------

        if index == 3:

            _save(
                entity_name,
                "nationality",
                place,
                memory
            )

        else:

            _save(
                entity_name,
                "birth_place",
                place,
                memory
            )

        break


    # ======================================================
    # AGE
    # ======================================================

    age_patterns = [

        r"(\d{1,3}) years old",

        r"age of (\d{1,3})",

        r"aged (\d{1,3})",

    ]

    for pattern in age_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            _save(
                entity_name,
                "age",
                match.group(1),
                memory
            )

            break


    # ======================================================
    # NET WORTH
    # ======================================================

    net_worth_patterns = [

        r"net worth (?:is|of|was|stands at)"
        r" (?:approximately |around |about )?"
        r"(\$?[\d,.]+ ?"
        r"(?:billion|million|trillion))",

        r"worth (?:approximately |around |about )?"
        r"(\$?[\d,.]+ ?"
        r"(?:billion|million|trillion))",

        r"net worth"
        r".{0,40}?"
        r"(\$?[\d,.]+ ?"
        r"(?:billion|million|trillion))",

    ]

    for pattern in net_worth_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            _save(
                entity_name,
                "net_worth",
                match.group(1),
                memory
            )

            break


    # ======================================================
    # RESIDENCE
    # ======================================================

    residence_patterns = [

        # lives in Austin, Texas
        r"lives in ([A-Z][A-Za-z .,'-]+?)(?:\.|, and| and|$)",

        # living in Austin, Texas
        r"living in ([A-Z][A-Za-z .,'-]+?)(?:\.|, and| and|$)",

        # resides in Austin, Texas
        r"resides in ([A-Z][A-Za-z .,'-]+?)(?:\.|, and| and|$)",

        # based in Austin, Texas
        r"based in ([A-Z][A-Za-z .,'-]+?)(?:\.|, and| and|$)",

        # based out of Austin, Texas
        r"based out of ([A-Z][A-Za-z .,'-]+?)(?:\.|, and| and|$)",

    ]

    for pattern in residence_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            _save(
                entity_name,
                "residence",
                match.group(1),
                memory
            )

            break


    # ======================================================
    # OCCUPATION
    # ======================================================
    entity_data = memory.get(
        "entities",
        {}
    ).get(
        entity_name,
        {}
    )
    entity_type = entity_data.get(
        "type",
        "unknown"
    )
    occupation_patterns = [

        r"is a ([A-Za-z -]+?)"
        r"(?:\.|, and| and| who| focused)",

        r"is an ([A-Za-z -]+?)"
        r"(?:\.|, and| and| who| focused)",

    ]

    if entity_type == "person":

        for pattern in occupation_patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                occupation = _clean_value(
                    match.group(1)
                )

                if occupation:

                    _save(
                        entity_name,
                        "occupation",
                        occupation,
                        memory
                    )

                break

    # ======================================================
    # COMPANY / ORGANIZATION EXTRACTION
    # ======================================================

    companies = []


    def add_company(company):
        """Clean and add one valid company without duplicates."""

        company = _clean_value(company)

        if not company:
            return

        company = company.strip(" .,;:")

        # Reject obvious sentence fragments
        invalid_starts = (
            "which ",
            "that ",
            "who ",
            "and ",
            "or ",
            "while ",
            "including ",
            "establishing ",
            "developing ",
            "designed ",
            "aims ",
        )

        if company.lower().startswith(invalid_starts):
            return

        # Reject obvious non-company phrases
        invalid_words = (
            "settlement",
            "satellites",
            "astronauts",
            "spacecraft",
            "orbit",
            "program",
            "technology",
            "rockets",
            "mission",
            "future",
            "energy",
        )

        if any(
            word in company.lower()
            for word in invalid_words
        ):
            return

        # Avoid duplicates
        if company.lower() not in [
            item.lower()
            for item in companies
        ]:
            companies.append(company)


    # ------------------------------------------------------
    # Split answer into sentences
    # ------------------------------------------------------

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )


    # ------------------------------------------------------
    # Search each sentence
    # ------------------------------------------------------

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue


        # ==================================================
        # FOUNDER OF
        # ==================================================

        matches = re.findall(
            r"\bfounder\s+of\s+"
            r"((?:The\s+)?"
            r"[A-Z][A-Za-z0-9&'.-]*"
            r"(?:\s+[A-Z][A-Za-z0-9&'.-]*)*)"
            r"(?=\s+(?:and|but|while)\b|[.!?,]|$)",
            sentence
        )

        for company in matches:
            add_company(company)


        # ==================================================
        # CO-FOUNDED COMPANY
        # ==================================================
        #
        # Examples:
        #
        # co-founded The Boring Company
        # co-founded SpaceX
        #
        # Capture the complete proper-name organization.
        # ==================================================

        matches = re.findall(
            r"\bco-founded\s+"
            r"((?:The\s+)?[A-Z][A-Za-z0-9&'.-]*"
            r"(?:\s+[A-Z][A-Za-z0-9&'.-]*)*)"
            r"(?=\s+(?:and|but|while|with)\b|[.!?,]|$)",
            sentence,
            re.IGNORECASE
        )

        for company in matches:
            add_company(company)


        

        # ==================================================
        # CO-FOUNDED
        # ==================================================

        matches = re.findall(
            r"\bco-founded\s+"
            r"((?:The\s+)?"
            r"[A-Z][A-Za-z0-9&'.-]*"
            r"(?:\s+[A-Z][A-Za-z0-9&'.-]*)*)"
            r"(?=\s+(?:and|but|while)\b|[.!?,]|$)",
            sentence
        )

        for company in matches:
            add_company(company)


        # ==================================================
    # FOUNDER OF OTHER COMPANIES, INCLUDING ...
    # ==================================================
    #
    # Example:
    #
    # founder of other notable companies, including
    # SpaceX, Neuralink, and The Boring Company
    #
    # This is deliberately restricted to sentences
    # containing "founder" + "companies".
    # ==================================================

    if (
        re.search(r"\bfounder\b", sentence, re.IGNORECASE)
        and re.search(r"\bcompanies\b", sentence, re.IGNORECASE)
        and re.search(r"\bincluding\b", sentence, re.IGNORECASE)
    ):

        including_match = re.search(
            r"\bincluding\s+(.+?)(?:[.!?]|$)",
            sentence,
            re.IGNORECASE
        )

        if including_match:

            company_text = including_match.group(1)

            # Stop before descriptive clauses
            company_text = re.split(
                r"\s+(?:which|where|who|that)\b",
                company_text,
                maxsplit=1,
                flags=re.IGNORECASE
            )[0]

            parts = re.split(
                r"\s*,\s*|\s+\band\s+",
                company_text,
                flags=re.IGNORECASE
            )

            for company in parts:

                company = company.strip()

                if not company:
                    continue

                add_company(company)


        # ==================================================
        # CEO OF
        # ==================================================

        matches = re.findall(
            r"\bCEO\s+of\s+"
            r"((?:The\s+)?[A-Z][A-Za-z0-9&'.-]*)",
            sentence,
            re.IGNORECASE
        )

        for company in matches:
            add_company(company)


        # ==================================================
        # CHIEF EXECUTIVE OFFICER OF
        # ==================================================

        matches = re.findall(
            r"\bchief\s+executive\s+(?:officer\s+)?of\s+"
            r"((?:The\s+)?[A-Z][A-Za-z0-9&'.-]*)",
            sentence,
            re.IGNORECASE
        )

        for company in matches:
            add_company(company)


    # ------------------------------------------------------
    # SAVE COMPANIES
    # ------------------------------------------------------

    if companies:

        _save(
            entity_name,
            "companies",
            ", ".join(companies),
            memory
        )

        # Remember discovered companies
        for company in companies:

            remember_reference(
                memory,
                "company",
                company
            )

        print(
            "[COMPANIES REFERENCES]:",
            companies
        )


# ==========================================================
# AGE FROM BIRTH DATE
# ==========================================================


def calculate_age_from_birth_date(
    birth_date
):
    """
    Calculate current age from a stored birth date.

    Returns:
        integer age
        or None if the date cannot be parsed.
    """

    if not birth_date:
        return None

    formats = [

        "%B %d, %Y",

        "%d %B %Y",

    ]

    parsed_date = None

    for fmt in formats:

        try:

            parsed_date = datetime.strptime(
                birth_date,
                fmt
            )

            break

        except ValueError:

            continue

    if not parsed_date:
        return None

    today = datetime.now()

    age = (
        today.year
        - parsed_date.year
    )

    birthday_this_year = (
        today.month,
        today.day
    ) >= (
        parsed_date.month,
        parsed_date.day
    )

    if not birthday_this_year:

        age -= 1

    return age