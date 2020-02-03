#!/usr/bin/env python


# In[1]:

import os
import json
import urllib.request
import csv
import pandas

import googlemaps
import pandas as pd

from django.conf import settings

from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2

gmap = googlemaps.Client(key=os.getenv('GOOGLE_MAP_API_KEY', 'AIzaSyAtJB-QRrG7kB1KoDgs7GI0k3H-_-R07HE'))


# In[2]:


def parse_csv(file_path, cols, depot):
    """
    function to parse whole csv file for the specified cols
    params:
    nrows = no. of rows to load in dataframe
    file_path = file path of csv file
    cols = list of column index/col name to parsen
    returns : DataFrame
    """
    try:
        df = pd.read_csv(file_path, nrows=500)
    except Exception:
        df = pd.read_csv(file_path, nrows=500, sep=';')
    if cols in df.columns:
        data = list(df[cols].values)
        #data.insert(0, depot)
    else:
        cols = df.columns.get_values()[1]
        data = list(df[cols].values)
        #data.insert(0, depot)

    df1 = pandas.DataFrame(data)
    #file exists?? random
    df1.to_csv("./file1.csv", sep=',',index=False)
    return data


# In[3]:


def pre_process_address(content):
    content = [x.replace(',', '') for x in content]
    content = [x.replace(' ', '+') for x in content]
    content = [x.strip() for x in content]
    return content


# In[4]:


def get_geocodes(data):
    geocodes = []
    address_omitted = []
    for index in range(len(data)):
        geocode_result = gmap.geocode(data[index])
        if len(geocode_result) > 0:
            temp = tuple(geocode_result[0]['geometry']['location'].values())
            geocodes.append(temp)
        else:
            geocodes.append(None)
            address_omitted.append(data[index])
    return geocodes, address_omitted


# In[5]:


def send_request(geocodes):
    """ Build and send request for the given origin and destination addresses."""

    def build_address_str(geocodes):
        # Build a pipe-separated string of addresses
        address_str = ''
        for i in range(len(geocodes) - 1):
            if geocodes[i]:
                address_str += str(geocodes[i][1]) + ',' + str(geocodes[i][0]) + ';'
        address_str += str(geocodes[-1][1]) + ',' + str(geocodes[-1][0])
        return address_str
    BACKEND_HOST = os.getenv('WEB_VRP_BACKEND_HOST', 'demo.rosebayconsult.com')
    BACKEND_PORT = os.getenv('WEB_VRP_BACKEND_PORT', '5000')

    request = 'http://' + BACKEND_HOST + ':' + BACKEND_PORT + '/table/v1/driving/'
    # request = 'https://router.project-osrm.org/table/v1/driving/'
    request = request + build_address_str(geocodes)
    json_result = urllib.request.urlopen(request).read()
    response = json.loads(json_result)
    return response


# In[6]:


"""Vehicles Routing Problem (VRP)."""


def create_data_model(dist_matrix, num_vehicles):
    """Stores the data for the problem."""
    data = {}
    data['distance_matrix'] = dist_matrix
    data['num_vehicles'] = num_vehicles
    data['depot'] = 0
    return data


def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    max_route_distance = 0
    result = list()
    result.clear()
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        per_result = []
        while not routing.IsEnd(index):
            plan_output += ' {} -> '.format(manager.IndexToNode(index))
            per_result.append(manager.IndexToNode(index))
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        plan_output += '{}\n'.format(manager.IndexToNode(index))
        per_result.append(manager.IndexToNode(index))
        plan_output += 'Distance of the route: {}m\n'.format(route_distance)
        print(plan_output)
        result.append(per_result)
        max_route_distance = max(route_distance, max_route_distance)
    print('Maximum of the route distances: {}m'.format(max_route_distance))
    df = pandas.DataFrame(result)
    df.to_csv("./file.csv", sep=',',index=False)

    """
    new code to save result
    """
    transpose_data = pd.read_csv(settings.BASE_DIR + '/file.csv')
    transpose_data = transpose_data.T 
    print(transpose_data.head())

    df = pd.read_csv(settings.BASE_DIR + "/file.csv")
    df1 = pd.read_csv(settings.BASE_DIR + "/file1.csv")

    new_df = df.replace(dict(enumerate(df1['0'])))
    new_df = new_df.T

    for column in new_df.columns:
        print(column)
        new_df.rename(columns={column: "Vehicle "+str(column)}, inplace=True)

    new_df.to_csv("media/result.csv", encoding='utf-8', sep=';', index=False, header=True)


    return result



def vrp_main(dist_matrix, num_vehicle):
    """Solve the CVRP problem."""
    # Instantiate the data problem.
    print("main started")
    data = create_data_model(dist_matrix, num_vehicle)

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    print('Transit callback: {}'.format(transit_callback_index))
    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint.
    dimension_name = 'Distance'
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        500000,  # vehicle maximum travel distance
        True,  # start cumul to zero
        dimension_name)
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.seconds = 30
    search_parameters.log_search = False
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem.
    print("Optimizing route...")
    solution = routing.SolveWithParameters(search_parameters)
    print("Done!")
    # Print solution on console.
    if solution:
        route_solution = print_solution(data, manager, routing, solution)
    else:
        print("No solutions")
        route_solution = None
    return route_solution


# In[7]:


def clean_result(result):
    for index, value in enumerate(result):
        if len(value) <= 2:
            print('ok')
            result.remove(value)
    return result


# In[8]:


def result_to_json(result, dist):
    fields = ['long', 'lat', 'key', 'address_id']
    test_dict = {}
    ctr = 0
    for i, l in enumerate(result):
        test_dict['vehicle' + str(i)] = []
        for j, addr_id in enumerate(l):
            temp_dict = dict(zip(fields, list(dist[addr_id]) + [ctr] + [addr_id]))
            test_dict['vehicle' + str(i)].append(temp_dict)
            ctr += 1
    y = json.dumps(test_dict)
    return y


# In[9]:


def process(filepath, num_vehicle, depot, cols='address'):
    data = {}
    try:
        data['address'] = parse_csv(filepath, cols, depot)
        pre_processed_address = pre_process_address(data['address'])
        data['geocodes'], data['omit_address'] = get_geocodes(pre_processed_address)
        response_osrm = send_request(data['geocodes'])
        dist_matrix = response_osrm['durations']
        print(dist_matrix)
        result = vrp_main(dist_matrix, num_vehicle)
        result = clean_result(result)
        response = result_to_json(result, data['geocodes'])
    except Exception as e:
        print(e)
        response = '{"status":"failed"}'

    return response


# transpose_data = pd.read_csv(settings.BASE_DIR + '/file.csv')
# transpose_data = transpose_data.T 
# print(transpose_data.head())


# df = pd.read_csv(settings.BASE_DIR + "/file.csv")
# df1 = pd.read_csv(settings.BASE_DIR + "/file1.csv")

# new_df = df.replace(dict(enumerate(df1['0'])))

# new_df.to_csv("result", sep='\t')

