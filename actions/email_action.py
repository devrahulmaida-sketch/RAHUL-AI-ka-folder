"""email_action.py"""
import os, urllib.parse


def email_action(parameters: dict, player=None) -> str:
    to      = parameters.get("to", "")
    subject = parameters.get("subject", "")
    body    = parameters.get("body", "")

    if not to:
        return "Recipient email required."

    # Open Gmail compose in browser
    encoded_sub  = urllib.parse.quote(subject)
    encoded_body = urllib.parse.quote(body)
    url = f"https://mail.google.com/mail/?view=cm&to={to}&su={encoded_sub}&body={encoded_body}"
    os.system(f"xdg-open '{url}' &")
    return f"Opened Gmail compose to: {to}"
