import socket
import psutil

# ============================================================
# JARVIS NETWORK INFORMATION SKILL — V7.4.2
# ============================================================

skill = {
    "name": "Network Information Skill",
    "priority": 24,
}


def can_handle(command):
    command = command.lower().strip()

    keywords = [
        "network status",
        "network information",
        "network info",
        "internet status",
        "internet connection",
        "check my internet",
        "am i connected",
        "is my internet working",
        "wifi status",
        "wi fi status",
        "what is my ip",
        "what's my ip",
        "ip address",
    ]

    return any(keyword in command for keyword in keywords)


def execute(command):
    try:
        hostname = socket.gethostname()

        local_ip = "Unavailable"

        try:
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            pass

        interfaces = psutil.net_if_stats()

        active_interfaces = []

        for name, stats in interfaces.items():
            if stats.isup:
                active_interfaces.append(name)

        if active_interfaces:
            connection_status = "Network interfaces are active."
        else:
            connection_status = "No active network interfaces were detected."

        interface_names = ", ".join(active_interfaces)

        return (
            f"Network status: {connection_status} "
            f"Local IP address is {local_ip}. "
            f"Active interfaces: {interface_names}."
        )

    except Exception as e:
        print("[NETWORK INFO ERROR]", e)
        return "I couldn't retrieve the network information."