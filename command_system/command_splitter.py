def split_commands(command):

    separators = [" and ", " then "]

    commands = [command]

    for sep in separators:

        temp = []

        for cmd in commands:
            temp.extend(cmd.split(sep))

        commands = temp

    commands = [c.strip() for c in commands if c.strip()]

    # ---- SMART ACTION INHERITANCE ----
    fixed_commands = []

    last_action = ""

    actions = [
        "open",
        "close",
        "increase",
        "decrease",
        "mute",
        "unmute",
        "play",
        "pause",
        "maximize",
        "minimize"
    ]

    for cmd in commands:

        words = cmd.split()

        if words and words[0] in actions:
            last_action = words[0]
            fixed_commands.append(cmd)

        else:
            if last_action:
                fixed_commands.append(f"{last_action} {cmd}")
            else:
                fixed_commands.append(cmd)

    return fixed_commands