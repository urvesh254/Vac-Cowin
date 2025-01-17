import datetime
import os
import sys

import requests

from utils.displayData import displayTable

BOOKING_URL = "https://cdn-api.co-vin.in/api/v2/appointment/schedule"
BENEFICIARIES_URL = "https://cdn-api.co-vin.in/api/v2/appointment/beneficiaries"
CALENDAR_URL_DISTRICT = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/calendarByDistrict?district_id={0}&date={1}"
CALENDAR_URL_PINCODE = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/calendarByPin?pincode={0}&date={1}"
CAPTCHA_URL = "https://cdn-api.co-vin.in/api/v2/auth/getRecaptcha"
OTP_PUBLIC_URL = "https://cdn-api.co-vin.in/api/v2/auth/public/generateOTP"
OTP_PRO_URL = "https://cdn-api.co-vin.in/api/v2/auth/generateMobileOTP"

WARNING_BEEP_DURATION = (1000, 2000)


try:
    import winsound

except ImportError:
    import os

    if sys.platform == "darwin":

        def beep(freq, duration):
            # brew install SoX --> install SOund eXchange universal sound sample translator on mac
            os.system(f"play -n synth {duration/1000} sin {freq} >/dev/null 2>&1")

    else:

        def beep(freq, duration):
            # apt-get install beep  --> install beep package on linux distros before running
            os.system("beep -f %s -l %s" % (freq, duration))


else:

    def beep(freq, duration):
        winsound.Beep(freq, duration)


def getPincodes():
    locations = []
    pincodes = input("Enter comma separated Pincodes to monitor (Priority wise): ")
    for idx, pincode in enumerate(pincodes.split(",")):
        pincode = {"pincode": pincode, "alert_freq": 440 + ((2 * idx) * 110)}
        locations.append(pincode)
    return locations


def getDistricts(request_header):
    """
    This function
        1. Lists all states, prompts to select one,
        2. Lists all districts in that state, prompts to select required ones, and
        3. Returns the list of districts as list(dict)
    """
    states = requests.get(
        "https://cdn-api.co-vin.in/api/v2/admin/location/states", headers=request_header
    )

    if states.status_code == 200:
        states = states.json()["states"]

        refined_states = []
        for state in states:
            tmp = {"state": state["state_name"]}
            refined_states.append(tmp)

        displayTable(refined_states)
        state = int(input("\nEnter State Index from the Table: "))
        state_id = states[state - 1]["state_id"]

        districts = requests.get(
            f"https://cdn-api.co-vin.in/api/v2/admin/location/districts/{state_id}",
            headers=request_header,
        )

        if districts.status_code == 200:
            districts = districts.json()["districts"]

            refined_districts = []
            for district in districts:
                tmp = {"district": district["district_name"]}
                refined_districts.append(tmp)

            displayTable(refined_districts)
            reqd_districts = input(
                "\nEnter comma separated index numbers of Districts to monitor : "
            )
            districts_idx = [int(idx) - 1 for idx in reqd_districts.split(",")]
            reqd_districts = [
                {
                    "district_id": item["district_id"],
                    "district_name": item["district_name"],
                    "alert_freq": 440 + ((2 * idx) * 110),
                }
                for idx, item in enumerate(districts)
                if idx in districts_idx
            ]

            print(f"Selected Districts are: ")
            displayTable(reqd_districts)
            return reqd_districts

        else:
            print("Unable to fetch the Districts...")
            print(districts.status_code)
            print(districts.text)
            os.system("pause")
            sys.exit(1)

    else:
        print("Unable to fetch the States...")
        print(states.status_code)
        print(states.text)
        os.system("pause")
        sys.exit(1)


def getBeneficiaries(request_header):
    """
    This function
        1. Fetches all beneficiaries registered under the mobile number,
        2. Prompts user to select the applicable beneficiaries, and
        3. Returns the list of beneficiaries as list(dict)
    """
    beneficiaries = requests.get(BENEFICIARIES_URL, headers=request_header)

    if beneficiaries.status_code == 200:
        beneficiaries = beneficiaries.json()["beneficiaries"]

        refined_beneficiaries = []
        for beneficiary in beneficiaries:
            beneficiary["age"] = datetime.datetime.today().year - int(
                beneficiary["birth_year"]
            )

            tmp = {
                "bref_id": beneficiary["beneficiary_reference_id"],
                "name": beneficiary["name"],
                "vaccine": beneficiary["vaccine"],
                "age": beneficiary["age"],
                "status": beneficiary["vaccination_status"],
            }
            refined_beneficiaries.append(tmp)

        displayTable(refined_beneficiaries)
        print(
            """
        ################# IMPORTANT THINGS TO BE REMEMBERED #################\n
        # 1. While selecting Beneficiaries, make sure that selected Beneficiaries are all taking the same dose: either their First OR Second.
        #    Please do no try to club together booking for first dose for one Beneficiary and second dose for another Beneficiary. Recommended to do both seperately.
        
        # 2. While selecting Beneficiaries, also make sure that Beneficiaries selected for second dose are all taking the same vaccine: COVISHIELD OR COVAXIN OR SPUTNIK V.
        #    Please do no try to club together booking for Beneficiary taking COVISHIELD with Beneficiary taking COVAXIN and other possibilities.
        
        # 3. If you're selecting multiple Beneficiaries, make sure all are of the same Age Group (45+ or 18+) as defined by the Government.
        #    Please do not try to club together booking for Younger and Older Beneficiaries at the same time.\n
        ###################################################333333333333333333
        """
        )
        reqd_beneficiaries = input(
            "Enter comma separated index numbers of Beneficiaries to book for : "
        )
        beneficiary_idx = [int(idx) - 1 for idx in reqd_beneficiaries.split(",")]
        reqd_beneficiaries = [
            {
                "bref_id": item["beneficiary_reference_id"],
                "name": item["name"],
                "vaccine": item["vaccine"],
                "age": item["age"],
                "status": item["vaccination_status"],
            }
            for idx, item in enumerate(beneficiaries)
            if idx in beneficiary_idx
        ]

        print(f"Selected Beneficiaries are: ")
        displayTable(reqd_beneficiaries)
        return reqd_beneficiaries

    else:
        print("Unable to Fetch Beneficiaries...")
        print(beneficiaries.status_code)
        print(beneficiaries.text)
        os.system("pause")
        return []


def getMinAge(beneficiary_dtls):
    """
    This function returns a min age argument, based on age of all beneficiaries
    :param beneficiary_dtls:
    :return: min_age:int
    """
    age_list = [item["age"] for item in beneficiary_dtls]
    min_age = min(age_list)
    return min_age
