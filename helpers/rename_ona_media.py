# Script to rename the flattened media export that Ona creates into subdirectories for each submission.
# This submission-specific subdir structure is required to correctly resubmit submissions that have attachments back into Kobo.
#
# This script must be run from the unzipped directory containing all the media files exported from the Ona form/project.
# After running it, all the media files should have been moved into their respective indexed submission subdir; if any files
# remain that means something went wrong.

import requests
import os
import json

# This is your personal Ona API access key. *** KEEP IT SECRET. DO NOT SHARE OR COMMIT! ***
# Find it under your Ona Profile -> Settings -> API
API_TOKEN="bef2c65372f06a8aff5ac51400388370f6328bde"

# This is the Ona ID of the source form.
# Called '_xform_id' in the export, or find it from the last component of the Overview URL; eg https://ona.io/bob/123/54321
FORM_ID="54321"

headers = {"Authorization": f"Token {API_TOKEN}"}
url = f"https://api.ona.io/api/v1/data/{FORM_ID}"  # API request to get *all* submissions (assume exported zip of all media)

response = requests.get(url, headers=headers)
if response.status_code == 200:
    for count,submission in enumerate(response.json()):
        #print(json.dumps(submission,indent=4))

        index = count+1  # submission indexes in a Ona data export XLSX start at 1

        # For each attachment of this submission, move the file into a subdir named after the index of the submission.
        # Note, filenames in the flattened Ona media export may have been renamed to ensure their uniqueness;
        # these must be renamed back to the filename used in the original submission for Kobo re-submission to work

        for item in submission['_attachments']:
            oldfile = os.path.basename(item['filename'])  # possibly renamed filename as it appears in the media export
            newfile = item['name']  # original filename used in the submission
            command = f"mkdir -p {index} && mv {oldfile} {index}/{newfile}"  # quick-n-dirty system() command...
            print(command)
            rc = os.system(command)
            if rc != 0:
                print(f"Failed to rename {oldfile}") 
else:
    print(f"Failed to fetch submissions: {response.status_code}")
