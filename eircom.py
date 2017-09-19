from peewee import *
import concurrent.futures
import multiprocessing
import re, requests, json
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

db = MySQLDatabase(host = 'localhost', port = 3306, user = 'root', database = 'eircom')
session = requests.Session()
retries = Retry(total = 10,
                backoff_factor = 3,
                status_forcelist = [ 500, 502, 503, 504 ])
session.mount('https://www.eirphonebook.ie', HTTPAdapter(max_retries = retries))

class Person(Model):
    id = CharField(max_length = 40, unique = True, primary_key = True)
    name = CharField(max_length = 60)
    address = CharField(max_length = 100)
    county = CharField(max_length = 12)
    allow_solicitation = BooleanField()
    area_code = CharField(max_length = 5)
    phone_number = CharField(max_length = 12, unique = True)

    class Meta:
        database = db

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:29.0) Gecko/20100101 Firefox/29.0',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive'
}

counties = {
    'Antrim',
    'Armagh',
    'Carlow',
    'Cavan',
    'Clare',
    'Cork',
    'Derry',
    'Donegal',
    'Down',
    'Dublin',
    'Fermanagh',
    'Galway',
    'Kerry',
    'Kildare',
    'Kilkenny',
    'Laois',
    'Leitrim',
    'Limerick',
    'Longford',
    'Louth',
    'Mayo',
    'Meath',
    'Monaghan',
    'Offaly',
    'Roscommon',
    'Sligo',
    'Tipperary',
    'Tyrone',
    'Waterford',
    'Westmeath',
    'Wexford',
    'Wicklow'
}

def main():
    # db.create_tables([Person], safe = True)
    with concurrent.futures.ProcessPoolExecutor(8) as executor:
        for county in counties:
            executor.submit(scrape_county, county)

def scrape_county(county):
    db.connect()
    page_num = 1
    person_count = 0
    retried_empty_count = 0
    while True:
        request_url = 'https://www.eirphonebook.ie/q/ajax/name?customerType=RESIDENTIAL&where=' + \
                        county + '&page=' + str(page_num) + '&searchType=DOUBLE&sort=az'
        print(request_url)
        response = session.get(request_url, headers = headers)
        response_json = json.loads(response.text)
        soup = BeautifulSoup(response_json['html'], 'html.parser')
        person_item_elems = soup.find_all('div', {'id': re.compile('^itembase\d+$'), 'data-customer': ''})
        if len(person_item_elems) == 0:
            if retried_empty_count < 5:
                retried_empty_count += 1 # Try again, up to 5 times. The server has been known to respond with blank pages randomly.
                continue
            break
        retried_empty_count = 0
        for person_item_elem in person_item_elems:
            person_count += 1
            item_id = int(person_item_elem['data-number'])
            person_id = person_item_elem['data-id']
            person_link_elem = person_item_elem.find('a', {'id': 'titlebase' + str(item_id)})
            person_name_elem = person_item_elem.find('span', {'id': 'listingbase' + str(item_id)})
            person_name = person_name_elem.text.strip()
            surname_match = re.match('businessNameClick,,([^,]+),', person_link_elem['data-wt'])
            if surname_match: # The below code swaps the firstname and surname so they're in the correct order.
                person_name = re.sub('(' + re.escape(surname_match.group(1)) + ') (.+)', r'\2 \1', person_name)
            print(person_name)
            person_address_elem = person_item_elem.find('div', {'class': 'result-address'})
            person_address = person_address_elem.text.strip()
            no_solicitation_elem = person_item_elem.find('span', {'class': 'no-sollicitation'})
            person_allow_solicitation = no_solicitation_elem == None
            person_phone_elem = person_item_elem.select('span[class="phone-number"]')
            if len(person_phone_elem) == 0: # Doesn't have a phone number associated.
                continue
            person_phone_elem = person_phone_elem[0]
            person_phone_match = re.match('\((\d+)\)(\d+)', person_phone_elem.text.strip())
            if not person_phone_match:
                person_name = person_name_elem.text.strip()
                continue
            person_area_code = person_phone_match.group(1)
            person_phone_number = person_phone_match.group(2)
            Person.insert(
                id = person_id, name = person_name, address = person_address, county = county,
                allow_solicitation = person_allow_solicitation, area_code = person_area_code, phone_number = person_phone_number
            ).upsert().execute()
        print(str(person_count)+' done so far')
        page_num += 1
    db.close()


if __name__ == '__main__':
    main()
