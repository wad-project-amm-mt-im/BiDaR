# from __future__ import print_function
import json
import urllib


def searchOnGoogle(querry: str, limit: int = 10) -> object:
    """
    This function will forrward the querry to Google KG API in order to get the big data requred
    @Params:
    @querry: The querry introduced by the user
    @returns: The result JSON-LD object received from Google KG
    """
    api_key = "AIzaSyC_ygBUVNG-9YRUk4hb8-ULNPaOH7mThIQ"
    service_url = 'https://kgsearch.googleapis.com/v1/entities:search'
    
    limit = min(limit, 100)
    params = {
        'query': querry,
        'limit': limit,
        'indent': True,
        'key': api_key,
    }
    url = service_url + '?' + urllib.parse.urlencode(params)
    response = urllib.request.urlopen(url).read()
    # for element in response['itemListElement']:
    #    print(element['result']['name'] + ' (' + str(element['resultScore']) + ')')
    # with open("./google_response.json", "w") as f:
    #    json.dump(response, f)
    # print("HERE:    " + json.dumps(response))
    return response
