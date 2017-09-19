import re
from peewee import *
from bs4 import BeautifulSoup

db = MySQLDatabase(host = 'localhost', port = 3306, user = 'root', database = 'eircom')

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
    #db.create_tables([Person], safe = True)
    area_code = input('Enter area code: ')
    phone_number = input('Enter phone number (without area code): ')
    try:
        person = Person.get(Person.area_code == area_code and Person.phone_number == phone_number)
    except Person.DoesNotExist:
        print('No user matches this phone number.')
        return
    print('URL: https://www.eirphonebook.ie/q/name/detail/{}/'.format(person.id))
    print('Name: ' + person.name)
    print('Address: ' + person.address)
    print('Solicitation allowed: ' + (person.allow_solicitation and 'yes' or 'no'))

if __name__ == '__main__':
    db.connect()
    main()
    db.close()