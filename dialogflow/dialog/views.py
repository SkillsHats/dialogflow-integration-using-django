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

from googletrans import Translator

# define home function 
def home(request):
    _html = """
    <div style="margin: 0px 35%">
        <iframe
            allow="microphone;"
            width="350"
            height="430"
            src="https://console.dialogflow.com/api-client/demo/embedded/26dd64a2-4638-439c-8278-5fd4b386ed5d">
        </iframe>
    </div>
    """

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


def get_current_location():
    url = "https://www.googleapis.com/geolocation/v1/geolocate?key="
    output = requests.post(url+settings.GOOGLE_MAP_KEY)
    response = output.json()

    return response

def get_lat():
    response = get_current_location()
    return response['location']['lat']

def get_lng():
    response = get_current_location()
    return response['location']['lng']

def get_formatted_address(gmaps, lat, lng):
    reverse_geocode_result = gmaps.reverse_geocode((lat, lng))
    current_location = reverse_geocode_result[0]['formatted_address']
    return current_location

def get_temperature(city_name):
    api_key = "369a7e29d89a64d59392e041482475ec"
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = base_url + "appid=" + api_key + "&q=" + city_name 
    
    response = requests.get(complete_url) 

    x = response.json() 
    
    if x["cod"] != "404": 
        y = x["main"]
        return y

    else: 
        print(" City Not Found ") 


def kelvin_to_celsius(kelvin):
    return round(kelvin - 273.15) 

@csrf_exempt
def new_webhook(request):
    req = json.loads(request.body)
    action = req.get('queryResult').get('action')
 
    # REVIEW INTENT
    if action == 'get_review':
        gmaps = googlemaps.Client(key=settings.GOOGLE_MAP_KEY)
        url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?'
        translator = Translator()
        text = req.get('queryResult').get('queryText')
        qrText = translator.translate(text)
        lngSrc = qrText.src

        if lngSrc != 'en':
            new_text = translator.translate(text, dest='en')
            text = new_text.text

        response =  requests.get(url + 'query=' + text + '&key=' + settings.GOOGLE_MAP_KEY) 
        outputs = response.json()

        name = outputs['results'][0]['name']
        address = outputs['results'][0]['formatted_address']
        rating = outputs['results'][0]['rating']
        place = outputs['results'][0]['place_id']

        if 'contact' in text.strip() or 'phone' in text.strip() or 'number' in text.strip():
            contact_url = 'https://maps.googleapis.com/maps/api/place/details/json?placeid='
            contact_res = requests.get(contact_url + place + '&rankby=distance&fields=formatted_phone_number&key=' + settings.GOOGLE_MAP_KEY)

            contact_output = contact_res.json()
            number = contact_output['result']['formatted_phone_number']
            output_msg = 'Nearby {} is at {}. Number is {}'.format(name, address, number)

            if lngSrc != 'en':
                new_text = translator.translate(output_msg, dest=lngSrc)
                reply = {'fulfillmentText': new_text.text}
                return JsonResponse(reply, safe=False)

            reply = {'fulfillmentText': output_msg}
            return JsonResponse(reply, safe=False)

        message = "{} is rated {} out of 5".format(name, rating)

        if lngSrc != 'en':
            new_text = translator.translate(message, dest=lngSrc)
            reply = {'fulfillmentText': new_text.text}
            return JsonResponse(reply, safe=False)

        reply = {'fulfillmentText': message}
        return JsonResponse(reply, safe=False)

    # DISTANCE INTENT
    if action == 'get_distance':
        gmaps = googlemaps.Client(key=settings.GOOGLE_MAP_KEY)
        translator = Translator()
        lat = get_lat()
        lng = get_lng()
        current_location = get_formatted_address(gmaps, lat, lng)

        text = req.get('queryResult').get('queryText')
        qrText = translator.translate(text)
        lngSrc = qrText.src

        if lngSrc != 'en':
            new_text = translator.translate(text, dest='en')
            text = new_text.text

        if 'from' in text and 'to' in text:
            tl = text.split("from")
            places = tl[1].split('to')
            dist = None
            if 'current' in places[0].strip():
                dist = gmaps.distance_matrix(current_location, places[1])['rows'][0]['elements'][0]

            dist = gmaps.distance_matrix(places[0], places[1])['rows'][0]['elements'][0]
            distance = dist['distance']['text']
            duration = dist['duration']['text']
            message ='{} by cab'.format(duration)

            if lngSrc != 'en':
                new_text = translator.translate(message, dest=lngSrc)
                reply = {'fulfillmentText': new_text.text}
                return JsonResponse(reply, safe=False)

            reply = {'fulfillmentText': message}
            return JsonResponse(reply, safe=False)

        if 'railway' in text:
            
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?"

            response =  requests.get(url + 'location=' + str(lat) +',' + str(lng) + '&rankby=distance&type=train_station&key=' + settings.GOOGLE_MAP_KEY) 
            outputs = response.json()

            stations = []

            for output in outputs['results'][:3]:
                dist = gmaps.distance_matrix(current_location, get_formatted_address(gmaps, output['geometry']['location']['lat'], output['geometry']['location']['lng']))['rows'][0]['elements'][0]
                stations.append({
                    "name": output['name'],
                    "dist": dist['distance']['text']
                })

            print(stations)

            reply = {"fulfillmentText": "test"}
            return JsonResponse(reply, safe=False)

        url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?'
        
        response =  requests.get(url + 'query=' + text + '&key=' + settings.GOOGLE_MAP_KEY) 
        outputs = response.json()
        
        fulfillmentText = 'Search Result'

        aog = actions_on_google_response()
        aog_sr = aog.simple_response([
            [fulfillmentText, fulfillmentText, False]
        ])
        
        cafes = []

        address = get_formatted_address(
                            gmaps, 
                            outputs['results'][0]['geometry']['location']['lat'], 
                            outputs['results'][0]['geometry']['location']['lng'])
        dist = gmaps.distance_matrix(
                    current_location, 
                    address)['rows'][0]['elements'][0]

        name = outputs['results'][0]['name']
        distance = dist['distance']['text']
        duration = dist['duration']['text']

        message = 'It is {} at {} and {} by cab'.format(distance, address, duration)

        if lngSrc != 'en':
            new_text = translator.translate(message, dest=lngSrc)
            reply = {'fulfillmentText': new_text.text}
            return JsonResponse(reply, safe=False)

        reply = {'fulfillmentText': message}

    if action == 'get_location':
        gmaps = googlemaps.Client(key=settings.GOOGLE_MAP_KEY)
        translator = Translator()

        text = req.get('queryResult').get('queryText')
        qrText = translator.translate(text)
        lngSrc = qrText.src

        lat = get_lat()
        lng = get_lng()
        current_location = get_formatted_address(gmaps, lat, lng)

        if lngSrc != 'en':
            new_text = translator.translate(current_location, dest=lngSrc)
            reply = {'fulfillmentText': new_text.text}
            return JsonResponse(reply, safe=False)

        reply = {'fulfillmentText': current_location}
    
    if action == 'get_places':
        gmaps = googlemaps.Client(key=settings.GOOGLE_MAP_KEY)

        lat = get_lat()
        lng = get_lng()
        current_location = get_formatted_address(gmaps, lat, lng)

        text = req.get('queryResult').get('queryText')

        translator = Translator()
        qrText = translator.translate(text)
        lngSrc = qrText.src

        if lngSrc != 'en':
            new_text = translator.translate(text, dest='en')
            text = new_text.text

        url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?'
        
        response =  requests.get(url + 'query=' + text + '&key=' + settings.GOOGLE_MAP_KEY) 
        outputs = response.json()
        
        hotels = []

        for output in outputs['results']:
            hotels.append(output['name'])

        if lngSrc != 'en':
            new_text = translator.translate(hotels, dest=lngSrc)
            reply = {'fulfillmentText': new_text[0].text + ", " + new_text[1].text + ", " + new_text[2].text}
            return JsonResponse(reply, safe=False)

        try:
            fulfillmentText = hotels[0] + ", " + hotels[1] + ", " + hotels[2]
        except:
            fulfillmentText = "Sorry, I didn't get it"

        aog = actions_on_google_response()
        aog_sr = aog.simple_response([
            [fulfillmentText, fulfillmentText, False]
        ])
        aog_sc = aog.suggestion_chips(hotels[:3])

        ff_response = fulfillment_response()
        ff_text = ff_response.fulfillment_text(fulfillmentText)
        ff_messages = ff_response.fulfillment_messages([aog_sr, aog_sc])

        reply = ff_response.main_response(ff_text, ff_messages)

    if action == 'get_temperature':
        translator = Translator()
        text = req.get('queryResult').get('queryText')
        qrText = translator.translate(text)
        lngSrc = qrText.src

        if lngSrc != 'en':
            new_text = translator.translate(text, dest='en')
            text = new_text.text

        city_name = "New Delhi"

        if "temperature at" in text:
            city = text.lower().split("temperature at")
            city_name = city[1].replace('?', '')

        elif "temperature in" in text:
            city = text.lower().split("temperature in")
            city_name = city[1].replace('?', '')

        temp = get_temperature(city_name)
        current_temperature = kelvin_to_celsius(temp["temp"])
        # current_pressure = temp["pressure"] 
        # current_humidiy = temp["humidity"] 
        message = str(current_temperature) + " degrees Celsius"

        if lngSrc != 'en':
            new_text = translator.translate(message, dest=lngSrc)
            reply = {'fulfillmentText': new_text.text}
            return JsonResponse(reply, safe=False)

        reply = {'fulfillmentText': message}

    return JsonResponse(reply, safe=False)

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
        reply = output

    if action == 'get_review':
        gmaps = googlemaps.Client(key=settings.GOOGLE_MAP_KEY)
        url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?'
        text = req.get('queryResult').get('queryText')
        response =  requests.get(url + 'query=' + text + '&key=' + settings.GOOGLE_MAP_KEY) 
        outputs = response.json()

        name = outputs['results'][0]['name']
        address = outputs['results'][0]['formatted_address']
        rating = outputs['results'][0]['rating']
        place = outputs['results'][0]['place_id']

        if 'contact' in text.strip() or 'phone' in text.strip() or 'number' in text.strip():
            contact_url = 'https://maps.googleapis.com/maps/api/place/details/json?placeid='
            contact_res = requests.get(contact_url + place + '&rankby=distance&fields=formatted_phone_number&key=' + settings.GOOGLE_MAP_KEY)

            contact_output = contact_res.json()
            number = contact_output['result']['formatted_phone_number']
            output_msg = 'Nearby {} is at {}. Number is {}'.format(name, address, number)
            reply = {'fulfillmentText': output_msg}
            return JsonResponse(reply, safe=False)

        message = "{} is rated {} out of 5".format(name, rating)
        reply = {'fulfillmentText': message}

    if action == 'get_distance':
        gmaps = googlemaps.Client(key=settings.GOOGLE_MAP_KEY)

        lat = get_lat()
        lng = get_lng()
        current_location = get_formatted_address(gmaps, lat, lng)

        text = req.get('queryResult').get('queryText')

        if 'from' in text and 'to' in text:
            tl = text.split("from")
            places = tl[1].split('to')
            dist = None
            if 'current' in places[0].strip():
                dist = gmaps.distance_matrix(current_location, places[1])['rows'][0]['elements'][0]

            dist = gmaps.distance_matrix(places[0], places[1])['rows'][0]['elements'][0]
            distance = dist['distance']['text']
            duration = dist['duration']['text']
            message ='{} by cab'.format(duration)
            reply = {'fulfillmentText': message}
            return JsonResponse(reply, safe=False)

        if 'railway' in text:
            
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?"

            response =  requests.get(url + 'location=' + str(lat) +',' + str(lng) + '&rankby=distance&type=train_station&key=' + settings.GOOGLE_MAP_KEY) 
            outputs = response.json()

            stations = []

            for output in outputs['results'][:3]:
                dist = gmaps.distance_matrix(current_location, get_formatted_address(gmaps, output['geometry']['location']['lat'], output['geometry']['location']['lng']))['rows'][0]['elements'][0]
                stations.append({
                    "name": output['name'],
                    "dist": dist['distance']['text']
                })

            print(stations)

            reply = {"fulfillmentText": "test"}
            return JsonResponse(reply, safe=False)

        url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?'
        
        response =  requests.get(url + 'query=' + text + '&key=' + settings.GOOGLE_MAP_KEY) 
        outputs = response.json()
        
        fulfillmentText = 'Search Result'

        aog = actions_on_google_response()
        aog_sr = aog.simple_response([
            [fulfillmentText, fulfillmentText, False]
        ])
        
        cafes = []

        address = get_formatted_address(
                            gmaps, 
                            outputs['results'][0]['geometry']['location']['lat'], 
                            outputs['results'][0]['geometry']['location']['lng'])
        dist = gmaps.distance_matrix(
                    current_location, 
                    address)['rows'][0]['elements'][0]

        name = outputs['results'][0]['name']
        distance = dist['distance']['text']
        duration = dist['duration']['text']

        message = 'It is {} at {} and {} by cab'.format(distance, address, duration)
        reply = {'fulfillmentText': message}


    if action == 'get_location':
        gmaps = googlemaps.Client(key=settings.GOOGLE_MAP_KEY)
        text = req.get('queryResult').get('queryText')

        lat = get_lat()
        lng = get_lng()
        current_location = get_formatted_address(gmaps, lat, lng)
        reply = {'fulfillmentText': current_location}

   
    if action == 'get_places':
        gmaps = googlemaps.Client(key=settings.GOOGLE_MAP_KEY)

        lat = get_lat()
        lng = get_lng()
        current_location = get_formatted_address(gmaps, lat, lng)

        text = req.get('queryResult').get('queryText')

        url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?'
        
        response =  requests.get(url + 'query=' + text + '&key=' + settings.GOOGLE_MAP_KEY) 
        outputs = response.json()
        
        hotels = []

        for output in outputs['results']:
            hotels.append(output['name'])


        fulfillmentText = hotels[0] + ", " + hotels[1] + ", " + hotels[2]

        aog = actions_on_google_response()
        aog_sr = aog.simple_response([
            [fulfillmentText, fulfillmentText, False]
        ])
        aog_sc = aog.suggestion_chips(hotels[:3])

        ff_response = fulfillment_response()
        ff_text = ff_response.fulfillment_text(fulfillmentText)
        ff_messages = ff_response.fulfillment_messages([aog_sr, aog_sc])

        reply = ff_response.main_response(ff_text, ff_messages)    

    # Temperature Intent
    if action == 'get_temperature':
        text = req.get('queryResult').get('queryText')

        city_name = "New Delhi"

        if "temperature at" in text:
            city = text.lower().split("temperature at")
            city_name = city[1].replace('?', '')

        elif "temperature in" in text:
            city = text.lower().split("temperature in")
            city_name = city[1].replace('?', '')

        temp = get_temperature(city_name)
        current_temperature = kelvin_to_celsius(temp["temp"])
        message = str(current_temperature) + " degrees Celsius"

        reply = {'fulfillmentText': message}

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