# pylint: disable-msg=C0103,R0913
"""
Python Client for Goibibo's API

https://developer.goibibo.com/docs
"""
import requests

class goibiboAPI(object):
    ''' Goibibo Py Client'''
    BASE = "http://developer.goibibo.com/api/"

    def __init__(self, app_id, app_key):
        self.auth = {"app_id" : app_id,
                    "app_key" : app_key}

    def FlightSearch(self, source, destination,
                    dateofdeparture, dateofarrival=None,
                    seatingclass="E", adults=1, children=0, infants=0):
        '''
        Search for operational flights based on specified parameters,
        i.e. route details, departure and arrival dates,
        cabin type and passenger details.

        Parameters
        ----------
        source : Origin Airport code. Valid IATA code
        destination : Destination Airport code. Valid IATA code
        dateofdeparture : Departure Date. Format (YYYYMMDD)
        dateofarrival : Arrival Date. Format (YYYYMMDD)
        seatingclass : Travel Class. E(Economy) or B(Business). Default - E
        adults : No of Adults. Int 1-9. Deafult - 1.
        children : No of children. Int 0-9. Deafult - 0.
        infants : No of infants. Int 0-9. Deafult - 0.

        Examples
        --------

            goibiboAPI.FlightSearch("BLR", "HYD", 20141028)
        '''

        if dateofarrival:
            dateda = "&dateofdeparture=%d\
                    &dateofarrival%d" % (dateofdeparture, dateofarrival)
        else:
            dateda = "&dateofdeparture=%d" % dateofdeparture

        return (requests.get(self.BASE + "search/" + "?format=json" +
                "&source=%s" % source + "&destination=%s" % destination +
                dateda +
                "&seatingclass=%s" % seatingclass +
                "&adults=%d" % adults +
                "&children=%d" % children + "&infants=%d" % infants,
                params=self.auth).json())

    def MinimumFare(self, source, destination, sdate, edate=None,
                    vertical="flight", mode=None, tclass=None):
        '''
        Gives you the details of flight/bus having minimum fare
        in a given sector and date range.

        Parameters
        ----------
        source : Origin Airport/City code.
                In case of flights, it should be a valid IATA code
        destination : Destination Airport/City code.
                    In case of flight, it should be a valid IATA code
        sdate : Starting of date range for which minimum fares are required
                (YYYYMMDD format)
        edate : Ending of date range for which minimum fares are required
                (YYYYMMDD format). Default value equals sdate
        vertical : The vertical for which minimum fare details are required.
                    Send 'flight' to get airline details and
                    'bus' for bus details.
                Default is flight.
        mode : Mode of result.
                'one' returns only one airline/bus per day which
                has the minimum fare.
                All returns minimum fares for all available
                airlines/buses per day.
            Default value is 'one'. Optional.
        class : Travel Class.
                NA(no filtering is done by class), E(Economy), B(Business).
                Default - NA. This parameter is applicable only for flights

        Examples
        --------

            goibiboAPI.MinimumFare("BLR", "HYD", 20141028)
        '''

        if edate:
            dateda = "&sdatte=%d&edate%d" % (sdate, edate)
        else:
            dateda = "&sdate=%d" % sdate
        strclass = "&vertical=%s" % vertical
        if mode:
            strclass = strclass + "&mode=" % mode
        if tclass:
            strclass = strclass + "&class=" % tclass

        return (requests.get(self.BASE + "stats/minfare/" + "?format=json" +
                "&source=%s" % source + "&destination=%s" % destination +
                strclass + dateda, params=self.auth).json())

    def BusSearch(self, source, destination,
                    dateofdeparture, dateofarrival=None):
        '''
        Provides available bus details operating in a given sector
        as per the chosen dates.

        Parameters
        ----------
        source : Origin city. Eg- bangalore
        destination : Destination city. Eg- hyderabad
        dateofdeparture : Date for onward bus journey. Format (YYYYMMDD)
        dateofarrival : Date for return bus journey. Format (YYYYMMDD).
                        Optional, required only for roundtrip journey.

        Examples
        --------

            goibiboAPI.BusSearch("bangalore", "hyderabad", 20141028)
        '''

        if dateofarrival:
            dateda = "&dateofdeparture=%d\
                    &dateofarrival%d" % (dateofdeparture, dateofarrival)
        else:
            dateda = "&dateofdeparture=%d" % dateofdeparture

        return (requests.get(self.BASE + "bus/search/" + "?format=json" +
                "&source=%s" % source + "&destination=%s" % destination +
                dateda, params=self.auth).json())

    def BusSeatMap(self, skey):
        '''
        Provides details of seat availablity and layout of a bus running
         on a particular sector on a given day.

         skey : Search key of the bus whose seat map is required.
                Search key is given by the bus search API for every bus.

        Examples
        --------

            goibiboAPI.BusSeatMap("vJ52KC0ymd0635qTD9bDDy9GHBkGl5FJMJje0aFX\
                                _GQTyev_4N9Y62TTfrmS-Re3dCHl0-UxLq4AsoQ%3D")
         '''

        return (requests.get(self.BASE + "bus/seatmap/" + "?format=json" +
                "&skey=%s" % skey,
                params=self.auth).json())

    def SearchHotelsByCity(self, city_id):
        '''
        Get a list of hotels available in a city alongwith
        information of each hotel.
        The full list of city ids can be found here.

        Parameters
        ----------
        method : Name of the method to call.
                In this case set it as 'hotels.get_hotels_data_by_city'
        city_id : City ID. Ex- Bangalore use 6771549831164675055 .
                The entire list of city ids is at 'Data' section.

        Examples
        --------

            goibiboAPI.SearchHotelsByCity(6771549831164675055)
        '''

        return (requests.get(self.BASE + "voyager/" +
                "?method=hotels.get_hotels_data_by_city" +
                "&city_id=%d" % city_id, params=self.auth).json())

    def GetHotelData(self, id_list):
        '''
        Get a list of hotels available in a city
        alongwith information of each hotel.

        Parameters
        ----------
        method : Type of response required
        id_list : List of hotel ids.
                Ex- '[1017089108070373346, 6085103403340214927]'
        id_type : The type of id being passed in 'id_list' parameter.
                You need to set it as '_id'

        Examples
        --------

            goibiboAPI.GetHotelData([1017089108070373346,
                                    6085103403340214927])
        '''

        id_list = str(id_list)\
                    .replace(" ", "")\
                    .replace("L", "")\
                    .replace(",", "%2C+")\
                    .replace("[", "%5B")\
                    .replace("]", "%5D")

        return (requests.get(self.BASE + "voyager/" +
                "?method=hotels.get_hotels_data" +
                "&id_list=%s" % id_list +
                "&id_type=_id", params=self.auth).json())

    def GetHotelPriceByCity(self, city_id, check_in, check_out):
        '''
        Fetches the price information of
        all the available hotels in the given city.
        The full list of city ids can be found here.

        Parameters
        ----------
        city_id : City ID of the city for which hotel prices are required.
                Ex- Bangalore use 6771549831164675055,
                                            .
                The full list of city ids can be found in 'Data' section.
        check_in : Hotel Check in date - format YYYYMMDD
        check_out : Hotel Check out date - format YYYYMMDD

        Examples
        --------

            goibiboAPI.GetHotelPriceByCity(6771549831164675055,
                                            20141101, 20141102)
        '''

        return (requests.get(self.BASE + "cyclone/" +
                "?city_id=%d" % city_id +
                "&check_in=%d" % check_in +
                "&check_out=%d" % check_out, params=self.auth).json())