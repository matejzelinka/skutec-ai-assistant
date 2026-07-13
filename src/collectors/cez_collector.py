import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CezCollector:

    BASE_URL = "https://api.bezstavy.cz/cezd/api/inspecttown"

    def __init__(self, town_id: int):
        self.town_id = town_id

    def fetch(self):
        url = f"{self.BASE_URL}/{self.town_id}"

        response = requests.get(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Skutec-AI-Assistant/1.0",
            },
            timeout=30,
            verify=False,
        )

        response.raise_for_status()

        data = response.json()

        print("API URL:", response.url)

        for outage in data.get("outages_in_town", []):
            print("PDF KEY:", outage.get("announcement_key"))
            print("OUTAGE KEYS:", list(outage.keys()))

        return data

    def outages(self):
        data = self.fetch()
        return data.get("outages_in_town", [])

    def normalize(self):
        result = []

        for outage in self.outages():

            event = {
                "id": outage["id"],
                "pdf": outage["announcement_key"],
                "from": outage["opened_at"],
                "to": outage["fix_expected_at"],
                "locations": [],
            }

            for town in outage["addresses"]["towns"]:

                if town["code"] != self.town_id:
                    continue

                town_name = town["name"]

                for district in town["town_districts"]:

                    for part in district["town_parts"]:

                        part_name = part["name"]

                        for street in part["streets"]:

                            event["locations"].append(
                                {
                                    "town": town_name,
                                    "part": part_name,
                                    "street": street["name"],
                                    "house_numbers": street["house_nums"],
                                    "ev_numbers": street["ev_nums"],
                                    "street_numbers": street["street_nums"],
                                }
                            )

            result.append(event)

        return result