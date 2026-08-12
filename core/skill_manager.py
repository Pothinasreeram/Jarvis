import importlib
import os

SKILLS = []

def load_skills():

    global SKILLS

    skills_folder = "skills"

    for file in os.listdir(skills_folder):

        if file.endswith("_skill.py"):

            module_name = file[:-3]

            try:

                module = importlib.import_module(
                    f"skills.{module_name}"
                )

                skill_data = {
                    "module": module,
                    "name": module.skill.get("name"),
                    "priority": module.skill.get("priority", 999)
                }

                SKILLS.append(skill_data)

                print(f"Loaded skill: {module_name}")

            except Exception as e:

                print(f"Failed loading {module_name}: {e}")

    # sort by priority
    SKILLS.sort(key=lambda s: s["priority"])


def execute_skill(command):

    print(f"[DEBUG] Executing command: {command}")

    for skill in SKILLS:

        module = skill["module"]

        print(f"[DEBUG] Checking {skill['name']}")

        try:

            if module.can_handle(command):

                print(f"[DEBUG] Matched {skill['name']}")

                return module.execute(command)

        except Exception as e:

            print("Skill Error:", e)

    print("[DEBUG] No skill matched")

    return None