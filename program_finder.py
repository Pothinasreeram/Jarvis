import os
import json

PROGRAM_PATHS = [
    "C:\\Program Files",
    "C:\\Program Files (x86)"
]

DATABASE_FILE = "programs.json"


def build_program_database():

    programs = {}

    for base_path in PROGRAM_PATHS:

        for root, dirs, files in os.walk(base_path):

            for file in files:

                if file.endswith(".exe"):

                    name = file.replace(".exe", "").lower()
                    full_path = os.path.join(root, file)

                    programs[name] = full_path

    with open(DATABASE_FILE, "w") as f:
        json.dump(programs, f, indent=4)

    print("Program database created.")


def load_program_database():

    if not os.path.exists(DATABASE_FILE):
        build_program_database()

    with open(DATABASE_FILE, "r") as f:
        return json.load(f)


def find_program(program_name):

    programs = load_program_database()

    program_name = program_name.lower().replace(" ", "")

    for name, path in programs.items():

        clean_name = name.lower().replace(" ", "")

        if program_name in clean_name or clean_name in program_name:
            return path

    return None