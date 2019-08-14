import os
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from library.df_response_lib import *
import json
import googlemaps
import dialogflow

import requests, json 

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

def getLocation():
    options = Options()
    options.add_argument("--use-fake-ui-for-media-stream")
    timeout = 20
    driver = webdriver.Chrome(executable_path = './chromedriver', chrome_options=options)
    driver.get("https://mycurrentlocation.net/")
    wait = WebDriverWait(driver, timeout)
    longitude = driver.find_elements_by_xpath('//*[@id="longitude"]')
    longitude = [x.text for x in longitude]
    longitude = str(longitude[0])
    latitude = driver.find_elements_by_xpath('//*[@id="latitude"]')
    latitude = [x.text for x in latitude]
    latitude = str(latitude[0])
    driver.quit()
    return (latitude,longitude)

# define home function 
def home(request):
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAP_KEY) 
    # reverse_geocode_result = gmaps.reverse_geocode(getLocation())
    # current_location = reverse_geocode_result[0]['formatted_address']
  
    # # # Requires cities name 
    # dist = gmaps.distance_matrix(current_location,'Pune')['rows'][0]['elements'][0] 
    
    # # Printing the result 
    # print(dist)
    # distance = dist['distance']['text']
    # duration = dist['duration']['text']

    url = "https://www.googleapis.com/geolocation/v1/geolocate?key="
    output = requests.post(url+settings.GOOGLE_MAP_KEY)
    response = output.json()
    lat = response['location']['lat']
    lng = response['location']['lng']
    reverse_geocode_result = gmaps.reverse_geocode((lat, lng))
    current_location = reverse_geocode_result[0]['formatted_address']
    print(current_location)

    # _html = """
    #     <iframe
    #         allow="microphone;"
    #         width="350"
    #         height="430"
    #         src="https://console.dialogflow.com/api-client/demo/embedded/26dd64a2-4638-439c-8278-5fd4b386ed5d">
    #     </iframe>
    # """

    _html = "Console"

    return HttpResponse( _html )


def detect_intent_texts(project_id, session_id, texts, language_code='en'):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'shyam-f369a086a7e2.json'

    import dialogflow_v2 as dialogflow
    session_client = dialogflow.SessionsClient()

    session = session_client.session_path(project_id, session_id)
    print('Session path: {}\n'.format(session))

    for text in texts:
        text_input = dialogflow.types.TextInput(
            text=text, language_code=language_code)

        query_input = dialogflow.types.QueryInput(text=text_input)

        response = session_client.detect_intent(
            session=session, query_input=query_input)

        print('=' * 20)
        print('Query text: {}'.format(response.query_result.query_text))
        print('Detected intent: {} (confidence: {})\n'.format(
            response.query_result.intent.display_name,
            response.query_result.intent_detection_confidence))
        print('Fulfillment text: {}\n'.format(
            response.query_result.fulfillment_text))


@csrf_exempt
def new_webhook(request):
    	# build request object
    req = json.loads(request.body)

    #get action from json
    action = req.get('queryResult').get('action')

    text       = req.get('queryResult').get('queryText')
    project_id = 'shyam-jgqxkh'
    session_id = 'ba059625-927f-e7fe-2eb2-b2ebbf5a3f87'

    output = detect_intent_texts(project_id, session_id, req)
    print(text)
    JsonResponse(output, safe=False)
        


@csrf_exempt
def webhook(request):
	# build request object
    req = json.loads(request.body)

    #get action from json
    action = req.get('queryResult').get('action')

    if action == 'get_test':
        text       = req.get('queryResult').get('queryText')
        project_id = 'shyam-jgqxkh'
        session_id = 'ba059625-927f-e7fe-2eb2-b2ebbf5a3f87'

        output = detect_intent_texts(project_id, session_id, req)
        print(output)
        reply = {'fullfillmentText': 'Working...'}
        
        # gmaps = googlemaps.Client(key=settings.GOOGLE_MAP_KEY)
        # dist = gmaps.distance_matrix('Delhi','Pune')['rows'][0]['elements'][0]
        # distance = dist['distance']['text']
        # duration = dist['duration']['text']
        # reply = {'fulfillmentText': 'Distance Between Delhi to Pune.', "distance": distance, "duration":duration}

    if action == 'get_location':
        gmaps = googlemaps.Client(key=settings.GOOGLE_MAP_KEY)

        current_loc = req.get('queryResult').get('parameters').get('location').get('city')
        destination = req.get('queryResult').get('parameters').get('destination')

        dist = gmaps.distance_matrix(current_loc, destination)['rows'][0]['elements'][0]

        '''
        text       = req.get('queryResult').get('queryText')
        project_id = 'shyam-jgqxkh'
        session_id = 'ba059625-927f-e7fe-2eb2-b2ebbf5a3f87'
        '''

        distance = dist['distance']['text']
        duration = dist['duration']['text']

        # geocode_result = gmaps.geolocate()
        # print(geocode_result)
        # output = detect_intent_texts(project_id, session_id, req)
        # reply = output
        reply = {'fulfillmentText': 'Distance.', "distance": distance, "duration":duration}

   
    if action == 'get_places':
        gmaps = googlemaps.Client(key=settings.GOOGLE_MAP_KEY)

        current_loc = req.get('queryResult').get('parameters').get('location')
        # print(current_loc['city'])

        url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?'

        response =  requests.get(url + 'query=restaurants+in+' + current_loc + '&key=' + settings.GOOGLE_MAP_KEY) 
        outputs = response.json()

        fulfillmentText = 'Nearest Restaurants'

        aog = actions_on_google_response()
        aog_sr = aog.simple_response([
            [fulfillmentText, fulfillmentText, False]
        ])
        
        hotels = []

        for output in outputs['results']:
            hotels.append(output['name'])
            
        dist = gmaps.distance_matrix(current_loc, hotels[0])['rows'][0]['elements'][0]
        distance = dist['distance']['text']
        duration = dist['duration']['text']

        r = "The nearest hotel to the location you are searching is {}, which is {} away and it will take {} to reach.".format(hotels[0], distance, duration)
        # r
        reply = {'fulfillmentText': r, "Distance": distance, "Duration": duration}
    

	# response for suggestion chips
    if action == 'get_suggestion_chips':

        # set fulfillment text
        fulfillmentText = 'Suggestion chips Response from webhook'

        aog = actions_on_google_response()
        aog_sr = aog.simple_response([
            [fulfillmentText, fulfillmentText, False]
        ])

        # create suggestion chips
        aog_sc = aog.suggestion_chips(["suggestion1", "suggestion2", "suggestion3"])

        ff_response = fulfillment_response()
        ff_text = ff_response.fulfillment_text(fulfillmentText)
        ff_messages = ff_response.fulfillment_messages([aog_sr, aog_sc])

        reply = ff_response.main_response(ff_text, ff_messages)
        

    # response for basic card
    if action == 'get_basiccard':

        fulfillmentText = 'Basic card Response from webhook'

        aog = actions_on_google_response()
        aog_sr = aog.simple_response([
            [fulfillmentText, fulfillmentText, False]
        ])

        basic_card = aog.basic_card("Title", "Subtitle", "This is formatted text", image=["https://www.google.com/wp-content/uploads/2018/12/logo-1024.png", "this is accessibility text"])

        ff_response = fulfillment_response()
        ff_text = ff_response.fulfillment_text(fulfillmentText)
        ff_messages = ff_response.fulfillment_messages([aog_sr, basic_card])

        reply = ff_response.main_response(ff_text, ff_messages)

    # response for link out suggestion
    if action == 'get_link':

        fulfillmentText = 'link out suggestion Response from webhook'

        aog = actions_on_google_response()
        aog_sr = aog.simple_response([
            [fulfillmentText, fulfillmentText, False]
        ])

        link_out_suggestion = aog.link_out_suggestion("Link Title", "https://google.com")

        ff_response = fulfillment_response()
        ff_text = ff_response.fulfillment_text(fulfillmentText)
        ff_messages = ff_response.fulfillment_messages([aog_sr, link_out_suggestion])

        reply = ff_response.main_response(ff_text, ff_messages)

    # response for list
    if action == 'get_list':

        fulfillmentText = 'List Response from webhook'

        aog = actions_on_google_response()
        aog_sr = aog.simple_response([
            [fulfillmentText, fulfillmentText, False]
        ])

        list_arr = [
            ["Title1", "Description1", ["item1", "item2"], ["https://www.pragnakalp.com/wp-content/uploads/2018/12/logo-1024.png", "Pragnakalp Techlabs"]],["Title2", "Description2", ["item1", "item2"], ["https://www.pragnakalp.com/wp-content/uploads/2018/12/logo-1024.png", "Pragnakalp Techlabs"]]
        ]

        list_select = aog.list_select("List Title", list_arr)

        ff_response = fulfillment_response()
        ff_text = ff_response.fulfillment_text(fulfillmentText)
        ff_messages = ff_response.fulfillment_messages([aog_sr, list_select])

        reply = ff_response.main_response(ff_text, ff_messages)

        return JsonResponse(reply, safe=False)

    # response for carousel card
    if action == 'get_carousel':

        fulfillmentText = 'Carousel card response from webhook'

        aog = actions_on_google_response()
        aog_sr = aog.simple_response([
            [fulfillmentText, fulfillmentText, False]
        ])

        carousel_arr = [
            ["Title1", "Description1", ["item1", "item2"], ["https://www.pragnakalp.com/wp-content/uploads/2018/12/logo-1024.png", "Pragnakalp Techlabs"]],["Title2", "Description2", ["item1", "item2"], ["https://www.pragnakalp.com/wp-content/uploads/2018/12/logo-1024.png", "Pragnakalp Techlabs"]]
        ]

        carousel_select = aog.carousel_select(carousel_arr)

        ff_response = fulfillment_response()
        ff_text = ff_response.fulfillment_text(fulfillmentText)
        ff_messages = ff_response.fulfillment_messages([aog_sr, carousel_select])

        reply = ff_response.main_response(ff_text, ff_messages)

        return JsonResponse(reply, safe=False)

    # response for Browse carousel card
    if action == 'get_browse_carousel':

        fulfillmentText = 'Browse carousel card response from webhook'

        aog = actions_on_google_response()
        aog_sr = aog.simple_response([
            [fulfillmentText, fulfillmentText, False]
        ])

        browse_carousel_arr = [
            ["Title1", ["https://www.pragnakalp.com/wp-content/uploads/2018/12/logo-1024.png", "title1"], "https://www.pragnakalp.com/blog"], ["Pragnakalp Techlabs", ["https://www.pragnakalp.com/wp-content/uploads/2018/12/logo-1024.png", "Pragnakalp Techlabs"], "https://www.pragnakalp.com/blog"]
        ]

        carousel_browse = aog.carousel_browse(browse_carousel_arr)

        ff_response = fulfillment_response()
        ff_text = ff_response.fulfillment_text(fulfillmentText)
        ff_messages = ff_response.fulfillment_messages([aog_sr, carousel_browse])

        reply = ff_response.main_response(ff_text, ff_messages)

        # return created response
    return JsonResponse(reply, safe=False)