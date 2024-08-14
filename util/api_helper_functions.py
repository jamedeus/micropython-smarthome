'''Utility functions used by both CLI tools and django backend to send bulk API
calls to lists of nodes.
'''


from concurrent.futures import ThreadPoolExecutor
from api_endpoints import (
    add_schedule_keyword,
    remove_schedule_keyword,
    save_schedule_keywords
)


def bulk_add_schedule_keyword(nodes, keyword, timestamp):
    '''Takes list of node IPs, new keyword name, new keyword timestamp.
    Makes parallel add_schedule_keyword API calls to all IPs in nodes list.
    '''
    commands = [(ip, [keyword, timestamp]) for ip in nodes]
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(add_schedule_keyword, *zip(*commands))


def bulk_remove_schedule_keyword(nodes, keyword):
    '''Takes list of node IPs, new keyword name, new keyword timestamp.
    Makes parallel remove_schedule_keyword API calls to all IPs in nodes list.
    '''
    commands = [(ip, [keyword]) for ip in nodes]
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(remove_schedule_keyword, *zip(*commands))


def bulk_edit_schedule_keyword(nodes, keyword_old, keyword_new, timestamp):
    '''Takes list of node IPs, existing keyword name, new keyword name, and new
    keyword timestamp. Makes parallel API calls to update keyword name and/or
    timestamp to all IPs in nodes list.
    '''

    # If keyword name did not change: Call add to overwrite existing timestamp
    if keyword_old == keyword_new:
        bulk_add_schedule_keyword(nodes, keyword_new, timestamp)

    # If keyword name changed: Remove existing keyword, add new keyword
    else:
        # Remove keyword from all nodes in parallel
        bulk_remove_schedule_keyword(nodes, keyword_old)

        # Add keyword to all nodes in parallel
        bulk_add_schedule_keyword(nodes, keyword_new, timestamp)


def bulk_save_schedule_keyword(nodes):
    '''Takes list of node IPs, makes parallel API calls to write current
    schedule keywords to disk.
    '''
    commands = [(ip, "") for ip in nodes]
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(save_schedule_keywords, *zip(*commands))
