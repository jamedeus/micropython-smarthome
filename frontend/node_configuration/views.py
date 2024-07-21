import json
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.templatetags.static import static
from .models import Node, Config, WifiCredentials, ScheduleKeyword, GpsCoordinates
from Webrepl import Webrepl
from provision_tools import get_modules, provision
from .get_api_target_menu_options import get_api_target_menu_options
from api_endpoints import add_schedule_keyword, remove_schedule_keyword, save_schedule_keywords, set_gps_coords
from validate_config import validate_full_config
from helper_functions import (
    valid_ip,
    get_schedule_keywords_dict,
    get_config_filename,
    get_device_and_sensor_metadata
)

# Env var constants
REPO_DIR = settings.REPO_DIR
NODE_PASSWD = settings.NODE_PASSWD


# Helper function for successful API responses
def standard_response(message, status=200):
    return JsonResponse(
        {'status': 'success', 'message': message},
        status=status
    )


# Helper function for error API responses
def error_response(message, status=400):
    return JsonResponse(
        {'status': 'error', 'message': message},
        status=status
    )


# Decorator used throw error if request is not POST
# Passes parsed JSON body to wrapped function as first arg
def requires_post(func):
    @wraps(func)
    def wrapper(request, **kwargs):
        if request.method == "POST":
            data = json.loads(request.body.decode("utf-8"))
        else:
            return error_response(message='Must post data', status=405)
        return func(data, **kwargs)
    return wrapper


@requires_post
def upload(data, reupload=False):
    if not valid_ip(data["ip"]):
        return error_response(message=f'Invalid IP {data["ip"]}', status=400)

    try:
        config = Config.objects.get(filename=data["config"])
    except Config.DoesNotExist:
        return error_response(
            message="Config file doesn't exist - did you delete it manually?",
            status=404
        )

    # Get dependencies, upload
    modules = get_modules(config.config, REPO_DIR)
    response = provision(data["ip"], NODE_PASSWD, config.config, modules)

    # If uploaded for the first time, update models
    if response['status'] == 200 and not reupload:
        new = Node.objects.create(
            friendly_name=config.config["metadata"]["id"],
            ip=data["ip"],
            floor=config.config["metadata"]["floor"]
        )

        config.node = new
        config.save()

    if response['status'] == 200:
        return standard_response(message=response['message'])
    else:
        return error_response(message=response['message'], status=response['status'])


def reupload_all(request):
    print("Reuploading all configs...")
    nodes = Node.objects.all()

    # Track success/failure of each upload
    report = {'success': [], 'failed': {}}

    for node in nodes:
        modules = get_modules(node.config.config, REPO_DIR)

        print(f"\nReuploading {node.friendly_name}...")
        response = provision(node.ip, NODE_PASSWD, node.config.config, modules)

        # Add result to report
        if response['status'] == 200:
            report['success'].append(node.friendly_name)
        elif response['status'] == 404:
            report['failed'][node.friendly_name] = 'Offline'
        elif response['status'] == 408:
            report['failed'][node.friendly_name] = 'Connection timed out'
        elif response['status'] == 409:
            report['failed'][node.friendly_name] = 'Filesystem error'

    print('\nreupload_all results:')
    print(json.dumps(report, indent=4))

    return standard_response(message=report)


@requires_post
def delete_config(data):
    try:
        # Get model entry
        target = Config.objects.get(filename=data)
    except Config.DoesNotExist:
        return error_response(
            message=f"Failed to delete {data}, does not exist",
            status=404
        )

    try:
        target.delete()
        return standard_response(message=f"Deleted {data}")
    except PermissionError:
        return error_response(
            message="Failed to delete, permission denied. This will break other features, check your filesystem permissions.",
            status=500
        )


@requires_post
def delete_node(data):
    try:
        # Get model entry
        node = Node.objects.get(friendly_name=data)
    except Node.DoesNotExist:
        return error_response(
            message=f"Failed to delete {data}, does not exist",
            status=404
        )

    try:
        # Delete from database and disk
        node.delete()
        return standard_response(message=f"Deleted {data}")
    except PermissionError:
        return error_response(
            message="Failed to delete, permission denied. This will break other features, check your filesystem permissions.",
            status=500
        )


@requires_post
def change_node_ip(data):
    if not valid_ip(data["new_ip"]):
        return error_response(
            message=f'Invalid IP {data["new_ip"]}',
            status=400
        )

    try:
        # Get model entry, delete from disk + database
        node = Node.objects.get(friendly_name=data['friendly_name'])
    except Node.DoesNotExist:
        return error_response(
            message="Unable to change IP, node does not exist",
            status=404
        )

    if node.ip == data["new_ip"]:
        return error_response(
            message='New IP must be different than old',
            status=400
        )

    # Get dependencies, upload to new IP
    modules = get_modules(node.config.config, REPO_DIR)
    response = provision(data["new_ip"], NODE_PASSWD, node.config.config, modules)

    if response['status'] == 200:
        # Update model
        node.ip = data["new_ip"]
        node.save()

        return standard_response(message="Successfully uploaded to new IP")
    else:
        return error_response(
            message=response['message'],
            status=response['status']
        )


def config_overview(request):
    context = {
        "not_uploaded": [],
        "uploaded": [],
        "schedule_keywords": [],
        "desktop_integration_link": static("node_configuration/micropython-smarthome-integration.zip")
    }

    # Reverse proxy connection: Add forwarded_for IP to context
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        context['client_ip'] = request.META.get('HTTP_X_FORWARDED_FOR')
    # Direct connection: Add client IP to context
    else:
        context['client_ip'] = request.META.get('REMOTE_ADDR')

    # Add all schedule rules except sunrise and sunset (can't edit) to context
    # Database key is used as react unique identifier
    for keyword in ScheduleKeyword.objects.all():
        if keyword.keyword != "sunrise" and keyword.keyword != "sunset":
            context["schedule_keywords"].append(
                {"id": keyword.pk, "keyword": keyword.keyword, "timestamp": keyword.timestamp}
            )

    not_uploaded = Config.objects.filter(node=None)

    for i in not_uploaded:
        context["not_uploaded"].append({
            'filename': i.filename,
            'friendly_name': i.config['metadata']['id']
        })

    uploaded = Node.objects.all()
    for i in uploaded:
        context["uploaded"].append({
            'friendly_name': i.friendly_name,
            'ip': i.ip,
            'filename': i.config.filename
        })

    print(json.dumps(context, indent=4))

    return render(request, 'node_configuration/overview.html', context)


# Returns context object with all device and sensor metadata keyed by _type param
# Used to populate configuration divs with appropriate inputs based on type
def get_metadata_context():
    # Get object containing all device/sensor metadata
    metadata = get_device_and_sensor_metadata()
    context = {'devices': {}, 'sensors': {}}

    # Iterate list of dicts, add each to dict with _type as key
    for i in metadata['devices']:
        context['devices'][i['config_name']] = i
    for i in metadata['sensors']:
        context['sensors'][i['config_name']] = i

    return context


def new_config(request):
    # Create context with config skeleton
    context = {
        "TITLE": "Create New Config",
        "config": {
            'metadata': {
                'id': '',
                'floor': '',
                'location': '',
                'schedule_keywords': get_schedule_keywords_dict()
            },
            'wifi': {
                'ssid': '',
                'password': ''
            },
        },
        "api_target_options": get_api_target_menu_options(),
        "metadata": get_metadata_context(),
        "edit_existing": False
    }

    # Add default wifi credentials if configured
    if len(WifiCredentials.objects.all()) > 0:
        default = WifiCredentials.objects.all()[0]
        context["config"]["wifi"]["ssid"] = default.ssid
        context["config"]["wifi"]["password"] = default.password

    print(json.dumps(context, indent=4))

    return render(request, 'node_configuration/edit-config.html', context)


def edit_config(request, name):
    try:
        target = Node.objects.get(friendly_name=name)
    except Node.DoesNotExist:
        return error_response(message=f'{name} node not found', status=404)

    # Load config from database
    config = target.config.config

    # Load device and sensor metadata
    metadata = get_metadata_context()

    # Build context object:
    # - IP and FILENAME: Used to reupload config
    # - NAME and TITLE: Used by django template
    # - edit_existing: Tells submit function to reupload config
    # - config: Full existing config object
    # - metadata: Device and Sensor metadata, determines input types for new cards
    # - api_target_options: Used to populate dropdowns in api-target rule modal
    context = {
        "IP": target.ip,
        "NAME": target.friendly_name,
        "TITLE": f"Editing {target.friendly_name}",
        "FILENAME": target.config.filename,
        "edit_existing": True,
        "config": config,
        "metadata": metadata,
        "api_target_options": get_api_target_menu_options(target.friendly_name)
    }

    print(json.dumps(context, indent=4))

    return render(request, 'node_configuration/edit-config.html', context)


# Return True if filename or friendly_name would conflict with an existing config or node
def is_duplicate(filename, friendly_name):
    # Check if filename will conflict with existing configs
    try:
        Config.objects.get(filename=filename)
        return True
    except Config.DoesNotExist:
        pass

    # Check if friendly name is a duplicate, must be unique for frontend
    try:
        Node.objects.get(friendly_name=friendly_name)
        return True
    except Node.DoesNotExist:
        return False


# Used to warn when duplicate name entered in config generator
@requires_post
def check_duplicate(data):
    friendly_name = data['name']
    filename = get_config_filename(friendly_name)

    if is_duplicate(filename, friendly_name):
        return error_response(
            message='Config already exists with identical name',
            status=409
        )
    else:
        return standard_response(message='Name available')


@requires_post
def generate_config_file(data, edit_existing=False):
    print("Input:")
    print(json.dumps(data, indent=4))

    # Cast floor to int (required by validator)
    # TODO does this really matter? Why was the validator added?
    data['metadata']['floor'] = int(data['metadata']['floor'])

    # Get filename (all lowercase, replace spaces with hyphens)
    filename = get_config_filename(data["metadata"]["id"])

    print(f"\nFilename: {filename}\n")

    # Confirm config exists when editing existing
    if edit_existing:
        try:
            model_entry = Config.objects.get(filename=filename)
        except Config.DoesNotExist:
            return error_response(message='Config not found', status=404)

    # Prevent overwriting existing config, unless editing existing
    if not edit_existing and is_duplicate(filename, data["metadata"]["id"]):
        return error_response(
            message='Config already exists with identical name',
            status=409
        )

    # If default location set, add coordinates to config
    if len(GpsCoordinates.objects.all()) > 0:
        location = GpsCoordinates.objects.all()[0]
        data["metadata"]["gps"] = {"lat": str(location.lat), "lon": str(location.lon)}

    print("Output:")
    print(json.dumps(data, indent=4))

    # Validate completed config, return error if invalid
    valid = validate_full_config(data)
    if valid is not True:
        print(f"\nERROR: {valid}\n")
        return error_response(message=valid, status=400)

    # If creating new config, add to models + write to disk
    if not edit_existing:
        new = Config.objects.create(config=data, filename=filename)
        new.write_to_disk()

    # If modifying old config, update JSON object and write to disk
    else:
        model_entry.config = data
        model_entry.save()

    return standard_response(message='Config created')


@requires_post
def set_default_credentials(data):
    # If default already set, overwrite
    if len(WifiCredentials.objects.all()) > 0:
        for i in WifiCredentials.objects.all():
            i.delete()

    new = WifiCredentials(ssid=data["ssid"], password=data["password"])
    new.save()

    return standard_response(message='Default credentials set')


@requires_post
def set_default_location(data):
    # If default already set, overwrite
    if len(GpsCoordinates.objects.all()) > 0:
        for i in GpsCoordinates.objects.all():
            i.delete()

    # Instantiate model
    GpsCoordinates.objects.create(display=data["name"], lat=data["lat"], lon=data["lon"])

    # Add coordinates to all existing nodes in parallel
    commands = [(node.ip, {'latitude': data["lat"], 'longitude': data["lon"]}) for node in Node.objects.all()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(set_gps_coords, *zip(*commands))

    # Add coordinates to all existing configs
    for config in Config.objects.all():
        config.config['metadata']['gps'] = {'lat': data['lat'], 'lon': data['lon']}
        config.save()

    return standard_response(message='Location set')


# Downloads config file from an existing node and saves to database + disk
@requires_post
def restore_config(data):
    if not valid_ip(data["ip"]):
        return error_response(message=f'Invalid IP {data["ip"]}', status=400)

    # Open conection, detect if node connected to network
    node = Webrepl(data["ip"], NODE_PASSWD)
    if not node.open_connection():
        return error_response(
            message='Unable to connect to node, please make sure it is connected to wifi and try again.',
            status=404
        )

    # Download config file from node, parse json
    config = node.get_file_mem("config.json")
    config = json.loads(config)

    # Get filename (all lowercase, replace spaces with hyphens)
    filename = get_config_filename(config["metadata"]["id"])

    # Prevent overwriting existing config
    if is_duplicate(filename, config['metadata']['id']):
        return error_response(
            message='Config already exists with identical name',
            status=409
        )

    # Overwrite schedule keywords with keywords from database
    config['metadata']['schedule_keywords'] = get_schedule_keywords_dict()

    # Confirm received config is valid
    valid = validate_full_config(config)
    if valid is not True:
        return error_response(
            message='Config format invalid, possibly outdated version.',
            status=500
        )

    # Create Config model entry
    config = Config(config=config, filename=filename)

    # Create Node model entry
    node = Node.objects.create(
        friendly_name=config.config["metadata"]["id"],
        ip=data["ip"],
        floor=config.config["metadata"]["floor"]
    )

    # Add reverse relation
    config.node = node
    config.save()

    response = {
        "friendly_name": node.friendly_name,
        "filename": node.config.filename,
        "ip": node.ip
    }
    return standard_response(message=response)


@requires_post
def add_schedule_keyword_config(data):
    # Create keyword in database
    try:
        ScheduleKeyword.objects.create(keyword=data["keyword"], timestamp=data["timestamp"])
    except ValidationError as ex:
        return error_response(message=str(ex), status=400)

    # Add keyword to all existing nodes in parallel
    commands = [(node.ip, [data["keyword"], data["timestamp"]]) for node in Node.objects.all()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(add_schedule_keyword, *zip(*commands))

    # Save keywords on all nodes
    save_all_schedule_keywords()

    # Add new keyword to all configs in database and on disk
    all_keywords = get_schedule_keywords_dict()
    for node in Node.objects.all():
        node.config.config['metadata']['schedule_keywords'] = all_keywords
        node.config.save()

    return standard_response(message='Keyword created')


@requires_post
def edit_schedule_keyword_config(data):
    try:
        target = ScheduleKeyword.objects.get(keyword=data["keyword_old"])
    except ScheduleKeyword.DoesNotExist:
        return error_response(message='Keyword not found', status=404)

    target.keyword = data["keyword_new"]
    target.timestamp = data["timestamp_new"]

    try:
        target.save()
    except ValidationError as ex:
        return error_response(message=str(ex), status=400)

    # If timestamp changed: Call add to overwrite existing keyword
    if data["keyword_old"] == data["keyword_new"]:
        # Update keyword on all existing nodes in parallel
        commands = [(node.ip, [data["keyword_new"], data["timestamp_new"]]) for node in Node.objects.all()]
        with ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(add_schedule_keyword, *zip(*commands))

    # If keyword changed: Remove existing keyword, add new keyword
    else:
        # Remove keyword from all existing nodes in parallel
        commands = [(node.ip, [data["keyword_old"]]) for node in Node.objects.all()]
        with ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(remove_schedule_keyword, *zip(*commands))

        # Add keyword to all existing nodes in parallel
        commands = [(node.ip, [data["keyword_new"], data["timestamp_new"]]) for node in Node.objects.all()]
        with ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(add_schedule_keyword, *zip(*commands))

    # Save keywords on all nodes
    save_all_schedule_keywords()

    # Update keywords for all configs in database and on disk
    all_keywords = get_schedule_keywords_dict()
    for node in Node.objects.all():
        node.config.config['metadata']['schedule_keywords'] = all_keywords
        node.config.save()

    return standard_response(message='Keyword updated')


@requires_post
def delete_schedule_keyword_config(data):
    try:
        target = ScheduleKeyword.objects.get(keyword=data["keyword"])
    except ScheduleKeyword.DoesNotExist:
        return error_response(message='Keyword not found', status=404)

    try:
        target.delete()
    except IntegrityError as ex:
        return error_response(message=str(ex), status=400)

    # Remove keyword from all existing nodes in parallel
    commands = [(node.ip, [data["keyword"]]) for node in Node.objects.all()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(remove_schedule_keyword, *zip(*commands))

    # Save keywords on all nodes
    save_all_schedule_keywords()

    # Remove keyword from all configs in database and from disk
    all_keywords = get_schedule_keywords_dict()
    for node in Node.objects.all():
        node.config.config['metadata']['schedule_keywords'] = all_keywords
        node.config.save()

    return standard_response(message='Keyword deleted')


# Call save_schedule_keywords for all nodes in parallel
def save_all_schedule_keywords():
    commands = [(node.ip, "") for node in Node.objects.all()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(save_schedule_keywords, *zip(*commands))
