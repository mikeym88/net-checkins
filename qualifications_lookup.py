"""Script that scrapes Amateur Radio Operator information from the ISED website."""

import re
import sys
from io import StringIO

import pandas as pd
import requests
from lxml import etree
from radio_operator import RadioOperator

if __name__ == "__main__":
    arguments = [cs.upper().strip() for cs in sys.argv[1:]]
    print(arguments)
    if not arguments:
        print("Please provide a call sign as an argument.")
        sys.exit(1)

    call_signs = [cs for cs in arguments if RadioOperator.validate_canadian_call_sign(cs) or RadioOperator.validate_american_call_sign(cs)]

    # Print invalid call signs
    for cl in arguments:
        if cl not in call_signs:
            print(f"Invalid call sign provided: {cl}")

    print(f"Valid call sign count: {len(call_signs)}")
    sys.exit(0)
    cs_info = []
    for cs in call_signs:
        print(f"Processing call sign: {cs}")
        operator = RadioOperator(cs)
        operator.get_canadian_call_sign_info(cs)
        qualifications = operator.get_qualifications()
        cs_info.append({
            "Full Name": info.get("full_name", ""),
            "Call Sign": info.get("call_sign", ""),
            "Honours": "Yes" if "Basic+" in qualifications else "No",
            "Advanced": "Yes" if "Advanced" in qualifications else "No",
            "Morse Code": "Yes" if "Morse Code" in qualifications else "No",
        })

    print("Done processing. Saving to CSV...")
    df = pd.DataFrame(cs_info)
    df.to_csv("amateur_qualifications.csv", index=False)
