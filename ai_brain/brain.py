import datetime
import webbrowser

from ai_brain.ai_brain import ask_ai
from ai_brain.internet_ai import search_internet
from ai_brain.personality import listening, acknowledgement, success, information

from memory_layer.memory import (
    remember_entity,
    get_current_entity,
    remember_entity_fact,
    recall_entity_fact,
    resolve_entity,
    save_memory,
    remember_reference,
    get_last_reference,
    get_last_reference_value,
    get_references
)

from memory_layer.fact_extractor import (
    extract_facts
)


# ==========================================================
# HELPERS
# ==========================================================

def _clean_command(command):
    """Normalize a command."""

    if not command:
        return ""

    return " ".join(
        command.lower().strip().split()
    )


def _resolve_pronouns(
    command,
    current_entity,
    memory
):
    """
    Resolve conversational references.

    Examples:

        he
        she
        him
        her
        his
        their
        they

    -> current entity

    And:

        it
        its
        that company
        this company
        the company
        that one
        this one

    -> most recent remembered reference
    """

    if not command:
        return command

    words = command.split()

    # ======================================================
    # REFERENCE MEMORY
    # ======================================================

    reference = get_last_reference(
        memory
    )

    reference_value = None
    reference_type = None

    if reference:

        reference_value = reference.get(
            "value"
        )

        reference_type = reference.get(
            "type"
        )

    # ======================================================
    # ENTITY PRONOUNS
    # ======================================================

    entity_pronouns = {
        "he",
        "she",
        "him",
        "her",
        "his",
        "their",
        "they"
    }

    # ======================================================
    # OBJECT REFERENCES
    # ======================================================

    object_pronouns = {
        "it",
        "its"
    }

    # ======================================================
    # PHRASE REFERENCES
    # ======================================================

    phrase_replacements = [
        "that company",
        "this company",
        "the company",
        "that one",
        "this one",
        "that business",
        "this business",
        "the business"
    ]

    original_command = command

    # ------------------------------------------------------
    # Resolve phrases first
    # ------------------------------------------------------

    if reference_value:

        for phrase in phrase_replacements:

            if phrase in command:

                command = command.replace(
                    phrase,
                    reference_value
                )

    # ------------------------------------------------------
    # Resolve object pronouns
    # ------------------------------------------------------

    if reference_value:

        resolved_words = []

        for word in command.split():

            if word in object_pronouns:

                resolved_words.append(
                    reference_value
                )

            else:

                resolved_words.append(
                    word
                )

        command = " ".join(
            resolved_words
        )

    # ------------------------------------------------------
    # Resolve person pronouns
    # ------------------------------------------------------

    if current_entity:

        resolved_words = []

        for word in command.split():

            if word in entity_pronouns:

                resolved_words.append(
                    current_entity
                )

            else:

                resolved_words.append(
                    word
                )

        command = " ".join(
            resolved_words
        )

    # ------------------------------------------------------
    # Print only if something changed
    # ------------------------------------------------------

    if command != original_command:

        print(
            "[REFERENCE RESOLVED]:",
            original_command,
            "->",
            command
        )

    return command

    # ------------------------------------------------------
    # Replace individual words
    # ------------------------------------------------------

    resolved_words = []

    for word in words:

        if word in pronouns:

            resolved_words.append(
                current_entity
            )

        else:

            resolved_words.append(
                word
            )

    command = " ".join(
        resolved_words
    )

    print(
        "[ENTITY RESOLVED]:",
        original_command,
        "->",
        command
    )

    return command


# ==========================================================
# ASK AI + MEMORY
# ==========================================================

def ask_and_remember(
    command,
    memory,
    entity=None
):
    """
    Ask AI, extract facts,
    and update conversational references.
    """

    answer = ask_ai(
        command,
        memory
    )

    if entity and answer:

        extract_facts(
            entity,
            answer,
            memory
        )

        # --------------------------------------------------
        # Keep entity as the active reference
        # Unless a more specific company reference
        # was already selected.
        # --------------------------------------------------

        last_reference = get_last_reference(
            memory
        )

        if not (
            last_reference
            and last_reference.get("type") == "company"
        ):

            remember_reference(
                memory,
                "entity",
                entity
            )

        save_memory(
            memory
        )

    return answer

# ==========================================================
# FACT QUESTION DETECTION
# ==========================================================

def detect_fact_question(command):
    """
    Detect which entity fact the user is asking for.

    Works with both:
        "where does he live"
        "where does elon musk live"

    and:
        "what does he do"
        "what does elon musk do"
    """

    command = _clean_command(command)

    if not command:
        return None

    # ======================================================
    # BIRTH PLACE
    # ======================================================

    birthplace_patterns = [
        "where was born",
        "where were born",
        "where is born",
        "where are born",
        "where did born",
        "place of birth",
        "birth place",
        "birthplace",
        "born where",
    ]

    if any(
        pattern in command
        for pattern in birthplace_patterns
    ):
        return "birth_place"

    # ======================================================
    # BIRTH DATE
    # ======================================================

    birth_date_patterns = [
        "when was born",
        "when were born",
        "when is born",
        "when are born",
        "when did born",
        "date of birth",
        "birth date",
        "birthday",
        "date born",
    ]

    if any(
        pattern in command
        for pattern in birth_date_patterns
    ):
        return "birth_date"

    # ======================================================
    # AGE
    # ======================================================

    age_patterns = [
        "how old",
        "what age",
        "age of",
        "his age",
        "her age",
        "their age",
        "age is",
    ]

    if any(
        pattern in command
        for pattern in age_patterns
    ):
        return "age"

    # ======================================================
    # NET WORTH
    # ======================================================

    net_worth_patterns = [
        "net worth",
        "how rich",
        "how wealthy",
        "worth",
        "wealth",
    ]

    if any(
        pattern in command
        for pattern in net_worth_patterns
    ):
        return "net_worth"

    # ======================================================
    # RESIDENCE
    # ======================================================

    residence_patterns = [
        "where does",
        "where do",
        "where is",
        "where are",
        "residence",
        "where lives",
        "living in",
        "based in",
    ]

    if any(
        pattern in command
        for pattern in residence_patterns
    ):
        if any(
            word in command
            for word in [
                "live",
                "lives",
                "living",
                "stay",
                "reside",
                "residence",
                "home",
                "based",
            ]
        ):
            return "residence"

        # ======================================================
    # OCCUPATION
    # ======================================================

    occupation_patterns = [
        "what does",
        "what do",
        "what is",
        "occupation",
        "profession",
        "career",
        "job",
        "work as",
        "works as",
    ]

    if any(
        pattern in command
        for pattern in occupation_patterns
    ):
        if any(
            word in command
            for word in [
                "do",
                "job",
                "occupation",
                "profession",
                "career",
                "work",
                "works",
            ]
        ):
            return "occupation"

    # ======================================================
    # COMPANIES
    # ======================================================

    company_patterns = [
        "what companies",
        "which companies",
        "what company",
        "which company",
        "what businesses",
        "which businesses",
        "companies does own",
        "companies do own",
        "companies does founded",
        "companies do founded",
        "companies he owns",
        "companies she owns",
        "companies he founded",
        "companies she founded",
        "businesses does own",
        "businesses do own",
    ]

    if any(
        pattern in command
        for pattern in company_patterns
    ):
        return "companies"

    return None


# ==========================================================
# DIRECT FACT ANSWER
# ==========================================================

def answer_from_memory(
    entity,
    fact_key,
    memory
):
    """
    Return a natural answer from stored memory.

    Returns None when the fact isn't stored.
    """

    if not entity:
        return None

    value = recall_entity_fact(
        memory,
        entity,
        fact_key
    )

    if not value:
        return None


    # ======================================================
    # BIRTH DATE
    # ======================================================

    if fact_key == "birth_date":

        return information(f"{entity} was born on {value}.")


    # ======================================================
    # BIRTH PLACE
    # ======================================================

    if fact_key == "birth_place":

        return information(f"{entity} was born in {value}.")


    # ======================================================
    # AGE
    # ======================================================

    if fact_key == "age":

        return information(f"{entity} is {value} years old.")


    # ======================================================
    # NET WORTH
    # ======================================================

    if fact_key == "net_worth":

        return information(f"{entity}'s net worth is {value}.")


    # ======================================================
    # RESIDENCE
    # ======================================================

    if fact_key == "residence":

        return information(f"{entity} lives in {value}.")


    # ======================================================
    # OCCUPATION
    # ======================================================

    if fact_key == "occupation":

        return information(f"{entity} is {value}.")


    # ======================================================
    # COMPANIES
    # ======================================================

    if fact_key == "companies":

        return information(f"{entity} is associated with {value}.")


    return None

def _remember_company_reference(
    command,
    memory
):
    """
    Detect a remembered company mentioned
    directly in the user's command.

    Example:

        "tell me about SpaceX"

    stores:

        company -> SpaceX
    """

    companies = get_references(
        memory,
        "company"
    )

    if not companies:
        return None

    command_lower = command.lower()

    # Prefer the longest company name first
    # to avoid partial matches.

    companies = sorted(
        companies,
        key=len,
        reverse=True
    )

    for company in companies:

        if company.lower() in command_lower:

            remember_reference(
                memory,
                "company",
                company
            )

            save_memory(
                memory
            )

            print(
                "[COMPANY REFERENCE SELECTED]:",
                company
            )

            return company

    return None

# ==========================================================
# MAIN COMMAND PROCESSOR
# ==========================================================

def process_command(
    command,
    memory,
    context
):

    command = _clean_command(
        command
    )

    if not command:

        return listening()


    # ======================================================
    # CURRENT ENTITY
    # ======================================================

    current_entity = get_current_entity(
        memory
    )

    if current_entity:

        print(
            "[ENTITY MEMORY]:",
            current_entity
        )


    # ======================================================
    # PRONOUN RESOLUTION
    # ======================================================

    resolved_command = _resolve_pronouns(
        command,
        current_entity,
        memory
    )

    _remember_company_reference(
        resolved_command,
        memory
    )


    # ======================================================
    # NEWS
    # ======================================================

    if (
        resolved_command == "news"
        or "latest news" in resolved_command
        or " news " in f" {resolved_command} "
    ):

        return search_internet(
            resolved_command
        )


    # ======================================================
    # NAME MEMORY
    # ======================================================

    if "my name is" in resolved_command:

        name = resolved_command.replace(
            "my name is",
            "",
            1
        ).strip()

        if name:

            memory["name"] = name

            save_memory(
                memory
            )

            return (
                f"Nice to meet you {name}."
            )

        return (
            "Please tell me your name."
        )


    if (
        "what is my name" in resolved_command
        or "what's my name" in resolved_command
    ):

        if "name" in memory:

            return (
                f"Your name is "
                f"{memory['name']}."
            )

        return (
            "I don't know your name yet."
        )


    # ======================================================
    # TIME
    # ======================================================

    if (
        resolved_command == "time"
        or "what time is it" in resolved_command
        or "current time" in resolved_command
    ):

        now = datetime.datetime.now().strftime(
            "%I:%M %p"
        )

        return (
            f"The time is {now}."
        )


    # ======================================================
    # OPEN YOUTUBE
    # ======================================================

    if "open youtube" in resolved_command:

        webbrowser.open(
            "https://youtube.com"
        )

        return (
            "Opening YouTube."
        )


    # ======================================================
    # ENTITY DETECTION
    # ======================================================

    if resolved_command.startswith(
        "who is"
    ):

        subject = resolved_command.replace(
            "who is",
            "",
            1
        ).strip()
        subject = subject.rstrip("?!.,;:")

        if subject:

            remember_entity(
                memory,
                subject,
                "person"
            )

            context["last_subject"] = subject

            current_entity = resolve_entity(
                memory,
                subject
            )

            print(
                "[ENTITY STORED]:",
                current_entity
            )

            save_memory(
                memory
            )

        return ask_and_remember(
            resolved_command,
            memory,
            current_entity
        )


    # ======================================================
    # TELL ME ABOUT
    # ======================================================

    if resolved_command.startswith(
        "tell me about"
    ):

        subject = resolved_command.replace(
            "tell me about",
            "",
            1
        ).strip()
        subject = subject.rstrip("?!.,;:")

        if subject:

            remember_entity(
                memory,
                subject,
                "unknown"
            )

            context["last_subject"] = subject

            current_entity = resolve_entity(
                memory,
                subject
            )

            save_memory(
                memory
            )

        return ask_and_remember(
            resolved_command,
            memory,
            current_entity
        )


    # ======================================================
    # EXPLICIT ENTITY QUESTION
    # ======================================================

    if resolved_command.startswith(
        "what is"
    ):

        words = resolved_command.split()

        possessive_words = {
            "his",
            "her",
            "their",
            "its"
        }

        has_possessive = any(
            word in possessive_words
            for word in words
        )

        if (
            not has_possessive
            and current_entity is None
        ):

            subject = resolved_command.replace(
                "what is",
                "",
                1
            ).strip()
            subject = subject.rstrip("?!.,;:")

            ignored_words = [

                "the time",

                "my name",

                "your name",

            ]

            if (
                subject
                and not any(
                    item in subject
                    for item in ignored_words
                )
            ):

                remember_entity(
                    memory,
                    subject,
                    "unknown"
                )

                context[
                    "last_subject"
                ] = subject

                current_entity = resolve_entity(
                    memory,
                    subject
                )

                save_memory(
                    memory
                )

        # --------------------------------------------------
        # Try stored fact first
        # --------------------------------------------------

        fact_key = detect_fact_question(
            resolved_command
        )

        if (
            current_entity
            and fact_key
        ):

            stored_answer = answer_from_memory(
                current_entity,
                fact_key,
                memory
            )

            if stored_answer:

                print(
                    "[MEMORY ANSWER]:",
                    stored_answer
                )

                return stored_answer

        return ask_and_remember(
            resolved_command,
            memory,
            current_entity
        )


    # ======================================================
    # STORED ENTITY FACT
    # ======================================================

    if current_entity:

        fact_key = detect_fact_question(
            resolved_command
        )

        if fact_key:

            stored_answer = answer_from_memory(
                current_entity,
                fact_key,
                memory
            )

            if stored_answer:

                print(
                    "[MEMORY ANSWER]:",
                    stored_answer
                )

                return stored_answer


    # ======================================================
    # AI FALLBACK
    # ======================================================

    return ask_and_remember(
        resolved_command,
        memory,
        current_entity
    )




