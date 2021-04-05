#################################
##### Name: Bulgan Jugderkhuu
##### Uniqname: bulgan
#################################

from bs4 import BeautifulSoup
import requests
import json
import time
import secrets # file that contains your API key

api_key = secrets.API_KEY

BASE_URL = 'https://www.nps.gov'
STATES_INDEX_PATH = '/index.htm'
CACHE_FILE_NAME = 'nps_cache.json'
CACHE_DICT = {}

def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary

    Parameters
    ----------
    None

    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache


def save_cache(cache):
    ''' Saves the current state of the cache to disk

    Parameters
    ----------
    cache_dict: dict
        The dictionary to save

    Returns
    -------
    None
    '''
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()


def make_url_request_using_cache(url, cache):
    '''Make a request to the Web API using the url if
    it is not already in the cache file

    Parameters
    ----------
    url: string
        The URL for the API endpoint
    cache: cache
        A dictionary of the cache

    Returns
    -------
    dict
        the data returned from making the request in the form of
        a dictionary
    '''
    if (url in cache.keys()): # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]

CACHE_DICT = open_cache()

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.

    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone


    def info(self):
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    index_url = BASE_URL + STATES_INDEX_PATH
    index_text = make_url_request_using_cache(index_url, CACHE_DICT)
    soup = BeautifulSoup(index_text, 'html.parser')


    states_dict = {}

    states_dropdown = soup.find(class_='dropdown-menu SearchBar-keywordSearch')
    states_list = states_dropdown.find_all('li')

    for state in states_list:
        state_link_tag = state.find('a')
        state_url_path = state_link_tag['href']
        state_url = BASE_URL + state_url_path
        state_name = state_link_tag.text.strip().lower()
        states_dict[state_name] = state_url
    return states_dict

def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and
    repeatably identify an API request by its baseurl and params

    AUTOGRADER NOTES: To correctly test this using the autograder, use an underscore ("_")
    to join your baseurl with the params and all the key-value pairs from params
    E.g., baseurl_key1_value1

    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs

    Returns
    -------
    string
        the unique key as a string
    '''


    param_strings = []
    connector = '_'
    for k in params.keys():
        param_strings.append(f'{k}_{params[k]}')
    param_strings.sort()
    unique_key = baseurl + connector +  connector.join(param_strings)
    return unique_key

def get_site_instance(site_url):
    '''Make an instances from a national site URL.

    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov

    Returns
    -------
    instance
        a national site instance
    '''
    #get the site page html
    site_text = make_url_request_using_cache(site_url, CACHE_DICT)
    site_soup = BeautifulSoup(site_text, 'html.parser')
    #extract the site information
    site_name = site_soup.find(class_='Hero-title').text.strip()
    site_category = site_soup.find(class_='Hero-designation').text.strip()
    try:
        site_city = site_soup.find('span', itemprop='addressLocality').text.strip()
        site_state = site_soup.find('span', itemprop='addressRegion').text.strip()
        site_address = site_city + ', ' + site_state
    except:
        site_address = 'No address'
    try:
        site_zip = site_soup.find('span', itemprop='postalCode').text.strip()
    except:
        site_zip = 'No zipcode'
    site_phone = site_soup.find('span', itemprop='telephone').text.strip()
    #create the national site instance
    site_instance = NationalSite(site_category, site_name, site_address, site_zip,site_phone)
    return site_instance


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.

    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov

    Returns
    -------
    list
        a list of national site instances
    '''
    list_of_sites = []

    state_text = make_url_request_using_cache(state_url, CACHE_DICT)
    state_soup = BeautifulSoup(state_text, 'html.parser')

    parks = state_soup.find_all('div', class_='col-md-9 col-sm-9 col-xs-12 table-cell list_left')
    for park in parks:
        park_link_tag = park.find('a')
        park_path = park_link_tag['href']
        park_url = BASE_URL + park_path
        site_instance = get_site_instance(park_url)
        list_of_sites.append(site_instance)
    return list_of_sites


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.

    Parameters
    ----------
    site_object: object
        an instance of a national site

    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    params = {
    'key': secrets.API_KEY,
    'origin': site_object.zipcode,
    'radius': 10,
    'units': 'm',
    'maxMatches': 10,
    'ambiguities': 'ignore',
    'outFormat': 'json'
}
    CACHE_DICT = open_cache()

    mapquest_url = 'http://www.mapquestapi.com/search/v2/radius'

    uniq_key = construct_unique_key(mapquest_url, params)
    if uniq_key in CACHE_DICT.keys():
        print('Using Cache')
        return CACHE_DICT[uniq_key]
    else:
        print('Fetching')
        CACHE_DICT[uniq_key] = requests.get(mapquest_url, params=params).json()
        save_cache(CACHE_DICT)
        return CACHE_DICT[uniq_key]


def formatted_nearby_places(api_resp):
    '''
    takes in an api response and prints
    the name, category, address and city
    of the up to 10 nearby places

    Parameters
    ----------
    api_resp: json
        the api response

    Returns
    -------
    '''

    results = api_resp['searchResults']
    for i in range(len(results)):
        name = results[i]['fields']['name']
        if results[i]['fields']['group_sic_code_ext']:
            category = results[i]['fields']['group_sic_code_name_ext']
        else:
            category = 'no category'
        if results[i]['fields']['address']:
            address = results[i]['fields']['address']
        else:
            address = 'no address'
        if results[i]['fields']['city']:
            city = results[i]['fields']['city']
        else:
            city = 'no city'
        print(f"- {name} ({category}): {address}, {city}")


def print_state_sites(state, sites_list):
    '''
    prints the state name and that state's sites
    ordered by their index in the list with
    relevant info

    Parameters
    ----------
    state: str
        the state name
    sites_list: list
        the list of sites

    Returns
    -------
    prints each site and it's index (starting at 1 not 0)

    '''
    print('-' * 50)
    print(f"List of national sites in {state.title()}")
    print('-' * 50)
    for x in sites_list:
        # print(sites_list.index(x)+1, x.info())
        print(f"[{sites_list.index(x)+1}]", x.info())


if __name__ == "__main__":
    # user_input = input("Enter a state name (e.g. Michigan, michigan), or 'exit' to quit: ").lower()
    states_dict = build_state_url_dict()
    while True:
        user_input = input("Enter a state name (e.g. Michigan, michigan), or 'exit' to quit: ").lower()
        if user_input == 'exit':
            break
        elif user_input in states_dict.keys():
            # states_dict = build_state_url_dict()
            user_input_state_url = states_dict[user_input]
            state_sites = get_sites_for_state(user_input_state_url)
            print_state_sites(user_input, state_sites)

            while True:
                try:
                    user_input = input("Choose the number for detail search or 'exit' or 'back': ")
                    if user_input == 'exit':
                        break
                    elif user_input == 'back':
                        break
                    if user_input.isnumeric():
                        if int(user_input) <= int(len(state_sites)):
                            choice_index = state_sites[int(user_input)-1]
                            nearby_list = get_nearby_places(choice_index)
                            print('-' * 50)
                            print(f"Places near {choice_index.name}")
                            print('-' * 50)
                            formatted_nearby_places(nearby_list)
                        else:
                            print("Index out of range. Please enter a new number")
                    else:
                        break
                except:
                    print("Error - please try again.")
        else:
            print("Error - enter a proper state name")
    print("Bye!")