from peewee import *
from bs4 import BeautifulSoup

db = SqliteDatabase('eircom.db')

class Person(Model):
    id = CharField(max_length = 40, unique = True)
    name = CharField(max_length = 60)
    address = CharField(max_length = 100)
    allow_sollicitation = BooleanField()
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
    phone_number = input('Enter phone number (with hyphen): ').strip().replace('(', '').replace(')', '-').replace(' ', '')
    try:
        person = Person.get(Person.phone_number == phone_number)
    except Person.DoesNotExist:
        print('No user matches this phone number.')
        return
    print('URL: https://www.eirphonebook.ie/q/name/detail/{}/'.format(person.id))
    print('Name: ' + person.name)
    print('Address: ' + person.address)
    print('Solicitation allowed: ' + (person.allow_sollicitation and 'yes' or 'no'))

if __name__ == '__main__':
    main()