def security_score(encryption):

    encryption = encryption.lower()

    if "wpa3" in encryption:
        return 100

    if "wpa2" in encryption:
        return 90

    if "wpa" in encryption:
        return 70

    if "wep" in encryption:
        return 30

    if (
        "open" in encryption
        or "none" in encryption
    ):
        return 0

    return 50


def security_label(score):

    if score >= 90:
        return "Strong"

    if score >= 70:
        return "Good"

    if score >= 40:
        return "Weak"

    return "Open / Unsafe"
