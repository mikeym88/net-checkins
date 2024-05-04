import requests
from lxml import etree
from io import StringIO
import re
from datetime import datetime
from requests.exceptions import ReadTimeout, ConnectTimeout
import copy

from typing import Optional

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, DateTime
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class RadioOperator(Base):
    __tablename__ = "checkins"

    id: Mapped[int] = mapped_column(primary_key=True)
    call_sign: Mapped[str] = mapped_column(String(32))
    full_name: Mapped[str] = mapped_column(String(1024))
    address: Mapped[Optional[str]] = mapped_column(String(1024))
    city: Mapped[Optional[str]] = mapped_column(String(1024))
    province: Mapped[Optional[str]] = mapped_column(String(1024))
    postal_code: Mapped[Optional[str]] = mapped_column(String(128))
    qualifications: Mapped[Optional[str]] = mapped_column(String(1024))
    status: Mapped[Optional[str]] = mapped_column(String(128))
    expiration_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    frn: Mapped[Optional[str]] = mapped_column(String(1024))
    checkin_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    repeater: Mapped[str] = mapped_column(String(32))

    def __init__(self, call_sign: str, repeater: str | None = None) -> None:
        user_info = None
        bare_user_info = {
            "full_name": None,
            "call_sign": call_sign,
            "address": None,
            "city": None,
            "province": None,
            "postal_code": None,
            "qualifications": None,
            "status": "",
            "expiration_date": None,
            "FRN": None
        }
        try:
            if self.validate_american_call_sign(call_sign):
                user_info = self.get_american_call_sign_info(call_sign)
            elif self.validate_canadian_call_sign(call_sign):
                user_info = self.get_canadian_call_sign_info(call_sign)
        except (ConnectTimeout, ReadTimeout) as e:
            print(f"Except: {str(e)}")
        finally:
            if not user_info:
                user_info = bare_user_info
            
        self.repeater = repeater
        self.checkin_date = datetime.now()
        self.set_user_info(user_info)
    
    def __str__(self):
        location = ""
        if self.city:
            location = f"{self.city}, {self.province}"
        else:
            location = f"{self.province}"
        return f"{self.full_name} ({self.call_sign}) from {location}."
    
    def set_user_info(self, user_info: dict) -> None:
        self.user_info = user_info
        self.call_sign = user_info["call_sign"].strip()
        self.full_name = user_info["full_name"].strip()
        self.address = user_info["address"].strip()
        if not self.address:
            self.address = None
        self.city = user_info["city"]
        if not self.city:
            self.city = None
        self.province = user_info["province"]
        self.postal_code = user_info["postal_code"]
        if not self.postal_code:
            self.postal_code = None
        self.qualifications = user_info["qualifications"]
        if not self.qualifications:
            self.qualifications = None
        self.status = user_info["status"]
        if not self.status:
            self.status = None
        self.expiration_date = user_info["expiration_date"]
        if not self.expiration_date:
            self.expiration_date = None
        self.frn = user_info["FRN"]
        if not self.frn:
            self.frn = None
    
    def operator_info(self) -> dict:
        return self.user_info

    @staticmethod
    def validate_american_call_sign(call_sign: str) -> bool | None:
        call_sign = call_sign.upper().strip().replace(" ", "").replace("-", "")
        if not call_sign:
            return False
        
        validation_rules = {
            "group_d_regex": "(K|W)[A-Z]\d[A-Z]{3}",
            "group_c_1_regex": "(K|N|W)\d[A-Z]{3}",
            "group_c_2_regex": "(KL|NL|WL|NP|WP|KH|NH|WH)\d[A-Z]{3}",
            "group_b_regex": "(K|N|W)[A-Z]\d[A-Z]{2}",
            "group_a_1_regex": "A[A-K]\d[A-Z]{2}",
            "group_a_2_regex": "(A[A-K]|K[A–Z]|N[A–Z]|W[A–Z])\d[A-Z]",
            "group_a_3_regex": "(K|N|W)\d[A-Z]{2}"
        }

        for _, rule in validation_rules.items():
            if re.match(rule, call_sign):
                return True
        
        return False
    
    @staticmethod
    def validate_canadian_call_sign(call_sign: str) -> bool:
        call_sign = call_sign.upper().strip().replace(" ", "").replace("-", "")
        if not call_sign:
            return False

        valid_canadian_prefixes = [
            "VE1", "VA1",  # Nova Scotia
            "VE2", "VA2",  # Quebec
            "VE3", "VA3",  # Ontario
            "VE4", "VA4",  # Manitoba
            "VE5", "VA5",  # Saskatchewan
            "VE6", "VA6",  # Alberta
            "VE7", "VA7",  # British Columbia
            "VE8",         # Northwest Territories
            "VE9",         # New Brunswick
            "VE0",         # International Waters
            "VO1",         # Newfoundland
            "VO2",         # Labrador
            "VY1",         # Yukon
            "VY2",         # Prince Edward Island
            "VY9",         # Government of Canada
            "VY0",         # Nunavut
            "CY0",         # Sable Is.
            "CY9",         # St-Paul Is.
        ]

        has_proper_prefix = call_sign.startswith(tuple(valid_canadian_prefixes))
        has_proper_format = re.match(r"^[A-Z]{2}\d[A-Z]{2,3}$", call_sign)

        return has_proper_format and has_proper_prefix

    @staticmethod
    def _state_abbreviation_to_full_name(state_abbreviation: str) -> str:
        if not state_abbreviation:
            return ""
        state_abbreviation = state_abbreviation.strip().upper()
        if len(state_abbreviation) != 2:
            return state_abbreviation
        abbrevations = {
            "AL": "Alabama",
            "AK": "Alaska",
            "AZ": "Arizona",
            "AR": "Arkansas",
            "AS": "American Samoa",
            "CA": "California",
            "CO": "Colorado",
            "CT": "Connecticut",
            "DE": "Delaware",
            "DC": "District of Columbia",
            "FL": "Florida",
            "GA": "Georgia",
            "GU": "Guam",
            "HI": "Hawaii",
            "ID": "Idaho",
            "IL": "Illinois",
            "IN": "Indiana",
            "IA": "Iowa",
            "KS": "Kansas",
            "KY": "Kentucky",
            "LA": "Louisiana",
            "ME": "Maine",
            "MD": "Maryland",
            "MA": "Massachusetts",
            "MI": "Michigan",
            "MN": "Minnesota",
            "MS": "Mississippi",
            "MO": "Missouri",
            "MT": "Montana",
            "NE": "Nebraska",
            "NV": "Nevada",
            "NH": "New Hampshire",
            "NJ": "New Jersey",
            "NM": "New Mexico",
            "NY": "New York",
            "NC": "North Carolina",
            "ND": "North Dakota",
            "MP": "Northern Mariana Islands",
            "OH": "Ohio",
            "OK": "Oklahoma",
            "OR": "Oregon",
            "PA": "Pennsylvania",
            "PR": "Puerto Rico",
            "RI": "Rhode Island",
            "SC": "South Carolina",
            "SD": "South Dakota",
            "TN": "Tennessee",
            "TX": "Texas",
            "TT": "Trust Territories",
            "UT": "Utah",
            "VT": "Vermont",
            "VA": "Virginia",
            "VI": "Virgin Islands",
            "WA": "Washington",
            "WV": "West Virginia",
            "WI": "Wisconsin",
            "WY": "Wyoming"
        }
        full_name = abbrevations.get(state_abbreviation)
        if not full_name:
            full_name = ""
        return full_name

    def get_american_call_sign_info(self, call_sign: str) -> dict:
        base_endpoint = "https://wireless2.fcc.gov/UlsApp/UlsSearch/"
        with requests.Session() as sess:
            call_sign = call_sign.strip().upper()
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Connection": "keep-alive",
                "Accept-Encoding": "gzip, deflate, br"
            }
            fcc_amateur_search_endpoint = base_endpoint + "searchAmateur.jsp"
            r = sess.get(fcc_amateur_search_endpoint, headers=headers)
            sess.cookies = r.cookies
            html = r.content.decode("utf-8")
            parser = etree.HTMLParser()
            tree = etree.parse(StringIO(html), parser)
            form_action = tree.xpath("//form[@name='amateurSearch']/@action")[0]
            print(f"Might need to send request to {form_action}")
            amateur_results_endpoint = base_endpoint + "results.jsp"
            
            # now_date = datetime.now().date().strftime("%m/%d/%Y")
            amateur_search_form_data = {
                "fiUlsExactMatchInd": "Y",
                "fiulsTrusteeName": "",
                "fiOwnerName": "",
                "fiUlsFRN": "",
                "fiCity": "",
                "ulsState": "",
                "fiUlsZipcode": "",
                "ulsCallSign": f"{call_sign}",
                "statusAll": "Y",
                "ulsDateType": "",
                "dateSearchType": "",
                "ulsFromDate": "",
                "ulsToDate": "",
                "fiRowsPerPage": "100",
                "ulsSortBy": "uls_l_callsign",
                "ulsOrderBy": "ASC",
                "Submit": "Submit",
                "hiddenForm": "hiddenForm",
                "jsValidated": "true"
            }
            post_headers = copy.deepcopy(headers)
            post_headers["Content-Type"] = "application/x-www-form-urlencoded"
            post_headers["Referer"] = fcc_amateur_search_endpoint
            post_headers["Accept-Encoding"] = "gzip, deflate, br, zstd"
            post_headers["Cache-Control"] = "max-age=0"
            post_headers["Origin"] = "https://wireless2.fcc.gov"
            operator_details = {}
            try:
                r = sess.post(amateur_results_endpoint,
                            data=amateur_search_form_data,
                            headers=post_headers,
                            timeout=(5, 30)
                            )
                html = r.content.decode("utf-8)").strip()
                tree = etree.parse(StringIO(html), parser)
                results_xpath = "//table[@summary='License search results']//tr[not(th)]"
                matches = tree.xpath(results_xpath)
                if not matches:
                    print(f"No matches found for {call_sign}")
                    return
                ham = matches[0]
                details_url = None
                # 0. Result number
                # 1. Call Sign/Lease ID	
                # 2. Name
                # 3. FRN
                # 4. Radio Service
                # 5. Status
                # 6. Expiration Date
                for i, e in enumerate(ham.xpath("./td")):
                    if i == 0:
                        continue
                    if i == 1:
                        path = e.xpath("./a/@href")
                        details_url = base_endpoint + path[0].strip()
                        operator_details["call_sign"] = e.xpath("./a/text()")[0].strip()
                    if i == 2:
                        full_name = e.xpath("./text()")[0]
                        operator_details["full_name"] = full_name.strip()
                    if i == 3:
                        frn = e.xpath("./text()")[0]
                        operator_details["FRN"] = frn.strip()
                    if i == 5:
                        status = e.xpath("./text()")[0]
                        operator_details["status"] = status.strip()
                    if i == 6:
                        expiration_date = e.xpath("./text()")[0]
                        expiration_date = expiration_date.strip()
                        expiration_date = datetime.strptime(expiration_date, "%m/%d/%Y")
                        operator_details["expiration_date"] = expiration_date
                
                r = sess.get(details_url,
                            headers=headers,
                            timeout=(5, 30)
                            )
                html = r.content.decode("utf-8)").strip()
                tree = etree.parse(StringIO(html), parser)

                # Extract Address
                address_xpath = "//tr[td/table//td/b[contains(text(), 'Licensee') and contains(text(), 'Information')]]/following-sibling::tr[1]//table//tr[3]/td[1]/text()"
                matches = tree.xpath(address_xpath)
                address_arr = []
                for match in matches:
                    component = match.strip()
                    if component and component != operator_details["full_name"]:
                        component = component.replace(",", "\n")
                        component = component.split("\n")
                        if type(component) == list:
                            address_arr += component
                        else:
                            address_arr.append(component)
                
                operator_details["address"], operator_details["city"], operator_details["province"], operator_details["postal_code"] = address_arr
                operator_details["province"] = self._state_abbreviation_to_full_name(operator_details["province"])
                
                # Get operator class
                class_xpath = "//tr[td/table//td/b[contains(text(), 'Amateur') and contains(text(), 'Data')]]/following-sibling::tr[1]//table//tr/td[contains(text(), 'Operator Class')]/following-sibling::td[1]/text()"
                class_matches = tree.xpath(class_xpath)
                technician_class = [x.strip() for x in class_matches if x.strip()]

                # Get operator group
                group_xpath = "//tr[td/table//td/b[contains(text(), 'Amateur') and contains(text(), 'Data')]]/following-sibling::tr[1]//table//tr/td[contains(text(), 'Group')]/following-sibling::td[1]/text()"
                group_match = tree.xpath(group_xpath)
                group = [x.strip() for x in group_match if x.strip()]
                qualifications = "".join(technician_class) + " - " + "Group " + "".join(group)
                operator_details["qualifications"] = qualifications
            except ConnectionError as e:
                print(f"ConnectionError: {str(e)}")
            except TimeoutError as e:
                print(f"TimeoutError: {str(e)}")
            except ReadTimeout as e:
                print(f"ReadTimeout: {str(e)}")
        
        return operator_details

    @staticmethod
    def get_canadian_call_sign_info(call_sign: str) -> dict | None:
        call_sign = call_sign.strip().upper()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "max-age=0"
        }
        amateur_results_endpoint = "https://apc-cap.ic.gc.ca/pls/apc_anon/query_amat_cs$callsign.actionquery"
        amateur_search_form_data = {
            "P_CALLSIGN": call_sign,
            "P_SURNAME": None,
            "P_CITY": None,
            "P_PROV_STATE_CD": None,
            "P_POSTAL_ZIP_CODE": None,
            "Z_ACTION": "QUERY",
            "Z_CHK": 0
        }
        response = requests.post(amateur_results_endpoint, headers=headers, data=amateur_search_form_data)
        html = response.content.decode("utf-8")
        details_url_pattern = r'<a href="(?P<details_url>.*)">' + call_sign.upper() + "</a>"
        details_url = re.search(details_url_pattern, html)
        if not details_url:
            print(f"No URL found for {call_sign}")
            return
        details_url = "https://apc-cap.ic.gc.ca/pls/apc_anon/" + details_url.group("details_url")
        details_url = details_url.replace("&amp;", "&")
        response = requests.get(details_url, headers=headers)
        html = response.content.decode("utf-8")
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(html), parser)

        call_sign = tree.xpath("//table//th[contains(text(),'Call Sign')]//following-sibling::td/text()")[0]
        name = tree.xpath("//table//th[contains(text(),'Name')]//following-sibling::td/text()")[0]
        address = tree.xpath("//table//th[contains(text(),'Address')]//following-sibling::td/text()")[0]
        city = tree.xpath("//table//th[contains(text(),'City')]//following-sibling::td/text()")[0]
        province = tree.xpath("//table//th[contains(text(),'Province')]//following-sibling::td/text()")[0]
        postal_code = tree.xpath("//table//th[contains(text(),'Postal Code')]//following-sibling::td/text()")[0]
        qualifications = tree.xpath("//table//th[contains(text(),'Qualifications')]//following-sibling::td/text()")[0]
        qualifications_arr = [q.strip() for q in qualifications.split(",")]
        basic_index = -1
        for i, q in enumerate(qualifications_arr):
            if q == "Basic with Honours":
                qualifications_arr[i] = "Basic+"
            if q == "Basic":
                basic_index = i
        if "Basic+" in qualifications_arr and basic_index >= 0:
            qualifications_arr.pop(basic_index)
        qualifications = ", ".join(qualifications_arr)

        return {
            "full_name": name.strip(),
            "call_sign": call_sign.strip(),
            "address": address.strip(),
            "city": city.strip(),
            "province": province.strip(),
            "postal_code": postal_code.strip(),
            "qualifications": qualifications.strip(),
            "status": "Active",
            "expiration_date": None,
            "FRN": None
        }

