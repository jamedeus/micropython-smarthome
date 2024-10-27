#!/usr/bin/env python3

'''A simple debugging script that calls the /mem_info endpoint on all nodes in
cli_config.json and prints a table for each mem_info parameter with the value
from each node and the average of all nodes.

Example output:

Total nodes: 7

free:
  bedroom:              47184
  downstairs-bathroom:  56736
  upstairs-bathroom:    60192
  kitchen:              58688
  bedroom-tv:           47744
  living-room:          53904
  thermostat:           59616
Average:                54866

max_new_split:
  bedroom:              22528
  downstairs-bathroom:  22528
  upstairs-bathroom:    22528
  kitchen:              22528
  bedroom-tv:           22528
  living-room:          22528
  thermostat:           22528
Average:                22528

max_free_sz:
  bedroom:               617
  downstairs-bathroom:  1406
  upstairs-bathroom:    1905
  kitchen:              1906
  bedroom-tv:            768
  living-room:          1185
  thermostat:            819
Average:                1229
'''

from api_client import parse_ip
from cli_config_manager import CliConfigManager

cli_config = CliConfigManager(no_sync=True)


def get_mem_info():
    '''Calls the mem_info endpoint on all nodes in cli_config.json.
    Returns a dict with node names as keys and responses as values.
    '''
    nodes = {}

    for node in cli_config.get_existing_node_names():
        response = parse_ip([node, 'mem_info'])
        if not str(response).startswith('Error'):
            nodes[node] = response

    return nodes


def get_average_param(report, param):
    '''Takes response from get_mem_info and name of one of the mem_info params.
    Totals the param from all node responses and returns average.
    '''
    total = 0
    nodes = 0
    for node in report:
        try:
            total += report[node][param]
            nodes += 1
        except (KeyError, TypeError):
            print(f'No mem_info for {node}')

    return int(total / nodes)


def print_node_param(report, param):
    '''Takes response from get_mem_info and name of one of the mem_info params.
    Prints table with name of each node and param value.
    '''

    # Find longest name and longest param value for spacing
    max_name_length = max(len(name) for name in report)
    max_num_length = max(len(str(response[param])) for response in report.values())

    print(f'{param}:')
    for name, response in report.items():
        # Print node name indented and left-aligned, param value right aligned
        print(f"  {name}:".ljust(max_name_length + 5) + str(response[param]).rjust(max_num_length))

    # Print average without indent
    average = get_average_param(report, param)
    print('Average:'.ljust(max_name_length + 5) + str(average).rjust(max_num_length) + '\n')


if __name__ == '__main__':
    result = get_mem_info()
    print(f'\nTotal nodes: {len(result)}\n')
    print_node_param(result, 'free')
    print_node_param(result, 'max_new_split')
    print_node_param(result, 'max_free_sz')
