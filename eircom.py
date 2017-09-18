from peewee import *
import re, requests, json
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

db = SqliteDatabase('eircom.db')
session = requests.Session()
retries = Retry(total = 5,
                backoff_factor = 3,
                status_forcelist = [ 500, 502, 503, 504 ])
session.mount('https://www.eirphonebook.ie', HTTPAdapter(max_retries = retries))

class Person(Model):
    id = CharField(max_length = 40, unique = True)
    name = CharField(max_length = 60)
    address = CharField(max_length = 100)
    allow_solicitation = BooleanField()
    phone_number = CharField(max_length = 16)

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
    db.connect()
    db.create_tables([Person], safe = True)
    for county in counties:
        scrape_county(county)

# TODO: Add multi-processing. Otherwise, this ends up taking hours to execute.

def scrape_county(county):
    with open('counties.txt', 'a+') as f:
        f.write(county + '\n')
    page_num = 1
    person_count = 0
    while True:
        request_url = 'https://www.eirphonebook.ie/q/ajax/name?customerType=RESIDENTIAL&where=' + \
                        county + '&page=' + str(page_num) + '&searchType=DOUBLE'
        print(request_url)
        response = session.get(request_url, headers = headers)
        response_json = json.loads(response.text)
        soup = BeautifulSoup(response_json['html'], 'html.parser')
        person_item_elems = soup.find_all('div', {'id': re.compile('^itembase\d+$'), 'data-customer': ''})
        if len(person_item_elems) == 0:
            break
        for person_item_elem in person_item_elems:
            item_id = int(person_item_elem['data-number'])
            person_id = person_item_elem['data-id']
            person_name_elem = person_item_elem.find('span', {'id': 'listingbase'+str(item_id)})
            person_name = person_name_elem.text.strip()
            print(person_name)
            person_address_elem = person_item_elem.find('div', {'class': 'result-address'})
            person_address = person_address_elem.text.strip()
            no_solicitation_elem = person_item_elem.find('span', {'class': 'no-sollicitation'})
            person_allow_solicitation = no_solicitation_elem == None
            person_phone_elem = person_item_elem.select('span[class="phone-number"]')[0]
            person_phone_number = person_phone_elem.text.strip().replace('(', '').replace(')', '-').replace(' ', '')
            Person.insert(
                id = person_id, name = person_name, address = person_address,
                allow_solicitation = person_allow_solicitation, phone_number = person_phone_number
            ).upsert().execute()
            person_count += 1
        print(str(person_count)+' done so far')
        page_num += 1

if __name__ == '__main__':
    main()