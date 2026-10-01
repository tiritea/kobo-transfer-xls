import glob
import io
import json
import os
import requests
import uuid
from datetime import datetime
from xml.etree import ElementTree as ET
import mimetypes
import time

from .media import get_media, del_media
from utils.text import get_valid_filename
from helpers.config import Config

def get_submission_edit_data():
    config = Config().dest
    _v_, v = get_info_from_deployed_versions()
    data = {
        'asset_uid': config['asset_uid'],
        'version': v,
        '__version__': _v_,
        'formhub_uuid': get_formhub_uuid(),
    }
    return data


def get_all_values_from_xml(elem):
    '''
    Return a list of all the values in the submission's XML
    '''
    values = []
    for child in elem:
        values.extend(get_all_values_from_xml(child))
    if elem.text:
        values.append(elem.text.strip())
    return [v for v in values if v]


def get_xml_value_media_mapping(values):
    '''
    Return a mapping of the filename as it's stored and the submission value
    as it's sent. We need this to link the two together again for when filenames
    are stripped of special characters.
    '''
    return {get_valid_filename(v):v for v in values}


def get_src_submissions_xml(xml_url):
    config = Config().src
    res = requests.get(
        url=xml_url, headers=config['headers'], params=config['params']
    )
    if not res.status_code == 200:
        raise Exception('Something went wrong')
    return ET.fromstring(res.text)


def submit_data(xml_sub, _uuid, original_uuid, xml_value_media_map):
    config = Config().dest
    MAX_SIZE = 100*1024*1024 # KPI client_max_body_size = 100M

    xml = io.BytesIO(xml_sub).getvalue() # may need to resend XML so persist the value
    file_tuple = (_uuid, xml)
    files = {'xml_submission_file': file_tuple}
    start_size = len(xml)
    size = start_size

    # see if there is media to upload with it
    submission_attachments_path = os.path.join(
        Config.ATTACHMENTS_DIR, Config().src['asset_uid'], original_uuid, '*'
    )
    print("looking for attachments in",submission_attachments_path)
    attachments = glob.glob(submission_attachments_path)
    with requests.Session() as session:
        while True:
            # Check if there are any remaining attachments to send
            if len(attachments):
                file_path = attachments[-1]  # last element is the one that will be pop()'d off
                filesize = os.path.getsize(file_path) + 1024 # add 1k per file overhead for boundary string, content-type, content-disposition...
                if size + filesize < MAX_SIZE:
                    size += filesize
                    filename = os.path.basename(file_path)
                    filename_value = xml_value_media_map.get(filename)
                    # check this file is actually referenced in the submission
                    if filename_value is not None:
                        mime_type, _ = mimetypes.guess_type(file_path)
                        if mime_type is not None:
                            files[filename_value] = (filename_value, open(file_path, 'rb'), mime_type)
                        else:
                            files[filename_value] = (filename_value, open(file_path, 'rb'))
                        print("+ adding",filename)
                    else:
                        print("- ignoring",filename,"as not in submission XML")
                    attachments.pop()
                    continue # keep adding attachments till hit MAX_SIZE

            req = requests.Request(
                method='POST',
                url=config['submission_url'],
                files=files,
                headers=config['headers'],
            )
            req_prep = req.prepare()

            retry = 5 # max number of retry attempts
            wait = 1 # starting wait time (x2 each attempt)
            while True: # keep trying if get 502/503/504 response
                res = session.send(req_prep)
                if (res.status_code in [502, 503, 504] and bool(retry)):
                    print(f'{res.status_code} response from server - retrying in {wait} seconds...')
                    time.sleep(wait)
                    wait *= 2
                    retry -= 1
                    continue
                elif (res.status_code // 100) != 2: # show response on fail for clues...
                    print(f'{res.status_code} response from server\n',res.text[:200]) # limit to 200 chars because 500 errors may return entire Kobo home page
                break

            # Abort on error or else stop POSTing when all attachments sent
            if (res.status_code // 100) != 2 or not(len(attachments)):
                break

            # Otherwise continue sending remaining attachments in followup POSTs
            files = {'xml_submission_file': file_tuple} # submission XML is always re-sent in OpenRosa
            size = start_size

    return res.status_code


def update_element_value(e, name, value):
    """
    Get or create a node and give it a value, even if nested within a group
    """
    el = e.find(name)
    if el is None:
        if '/' in name:
            root, node = name.split('/')
            el = ET.SubElement(e.find(root), node)
        else:
            el = ET.SubElement(e, name)
    el.text = value


def update_root_element_tag_and_attrib(e, tag, attrib):
    """
    Update the root of each submission's XML tree
    """
    e.tag = tag
    e.attrib = attrib


def generate_new_instance_id() -> (str, str):
    """
    Returns:
        - Generated uuid
        - Formatted uuid for OpenRosa xml
    """
    _uuid = str(uuid.uuid4())
    return _uuid, f'uuid:{_uuid}'


def transfer_submissions(all_submissions_xml, asset_data, quiet, regenerate):
    results = []
    count = len(all_submissions_xml)
    for i, submission_xml in enumerate(all_submissions_xml, start=1):

        # Use the same UUID so that duplicates are rejected
        original_uuid = submission_xml.find('meta/instanceID').text.replace(
            'uuid:', ''
        )
        if regenerate:
            _uuid, formatted_uuid = generate_new_instance_id()
            submission_xml.find('meta/instanceID').text = formatted_uuid
        else:
            _uuid = original_uuid

        new_attrib = {
            'id': asset_data['asset_uid'],
            'version': asset_data['version'],
        }
        update_root_element_tag_and_attrib(
            submission_xml, asset_data['asset_uid'], new_attrib
        )
        update_element_value(
            submission_xml, '__version__', asset_data['__version__']
        )
        update_element_value(
            submission_xml, 'formhub/uuid', asset_data['formhub_uuid']
        )

        submission_values = get_all_values_from_xml(submission_xml)
        xml_value_media_map = get_xml_value_media_mapping(submission_values)

        # Uncomment the following to see the actual submission XML being sent, for debugging
        """
        ET.indent(submission_xml)
        print("submission XML:\n",ET.tostring(submission_xml, encoding='unicode'))
        """
        result = submit_data(
            ET.tostring(submission_xml),
            _uuid,
            original_uuid,
            xml_value_media_map,
        )
        if result == 201:
            msg = f'✅ {_uuid} ({i}/{count})'
        elif result == 202:
            msg = f'⚠️  {_uuid} ({i}/{count})'
        else:
            deprecated_uuid = submission_xml.find('meta/deprecatedID')
            if deprecated_uuid is not None:
                msg = f'❌ {_uuid} ({i}/{count}, was {deprecated_uuid.text.replace("uuid:", "")})' # indicate which existing submission failed to update
            else:
                msg = f'❌ {_uuid} ({i}/{count})'
            log_failure(_uuid)
        if not quiet:
            print(msg)
        results.append(result)
    return results


def log_failure(_uuid):
    with open(Config.FAILURES_LOCATION, 'a') as f:
        f.write(f'{_uuid}\n')


def get_formhub_uuid():
    config = Config().dest
    res = requests.get(
        url=config['asset_url'],
        headers=config['headers'],
        params=config['params'],
    )
    if not res.status_code == 200:
        raise Exception('Something went wrong')
    return res.json()['deployment__uuid']


def get_deployed_versions():
    config = Config().dest
    res = requests.get(
        url=config['asset_url'],
        headers=config['headers'],
        params=config['params'],
    )
    if not res.status_code == 200:
        raise Exception('Something went wrong')
    data = res.json()
    return data['deployed_versions']


def format_date_string(date_str):
    """
    Format goal: "1 (2021-03-29 19:40:28)"
    """
    date, time = date_str.split('T')
    return f"{date} {time.split('.')[0]}"


def get_info_from_deployed_versions():
    """
    Get the version formats
    """
    deployed_versions = get_deployed_versions()
    count = deployed_versions['count']

    latest_deployment = deployed_versions['results'][0]
    date = latest_deployment['date_deployed']
    version = latest_deployment['uid']

    return version, f'{count} ({format_date_string(date)})'


def print_stats(results):
    total = len(results)
    success = results.count(201)
    skip = results.count(202)
    fail = total - success - skip
    print(f'🧮 {total}\t✅ {success}\t⚠️ {skip}\t❌ {fail}')
