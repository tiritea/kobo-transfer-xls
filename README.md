# Setup
Clone this repo to your system with the following command:

  `git clone https://github.com/tiritea/kobo-transfer-xls.git`

Copy the sample config file to customise to your Kobo account:

  `cp kobo-transfer-xls/sample-config.json kobo-transfer-xls/config.json`

There are some additional python environment pre-requisites described in `kobo-transfer-xls/xls_transfer/README.md`

# Configuration
Edit `kobo-transfer-xls/config.json` with your Kobo project and account settings. Add these for both the `src` (source) and `dest` (destination) JSON settings [when using the tool to create *new* submissions from XLSX the `src` isnt required].
- get `kc_url` from **FORM** -> **Collect data** -> **Android application** (eg https://kc.kobotoolbox.org)
- get `kf_url` from any project page URL prefix (eg https://kf.kobotoolbox.org)
- get the `token` from your **Account** -> **Account settings** -> **Security** page. Hit the **Display** button and then copy the **API Key** value.
- get the `asset_uid` from the project summary page URL (eg kf.kobotoolbox.org/#/forms/**a7d7KzP5YJ9d9fhdWyGNtJ**/summary). Please note a new project must first be deployed before you can upload submissions against it; if you forget you'll almost immediately get an obscure fatal runtime error when running the tool.

# Usage
Export submissions from your Kobo project's DATA tab with the following Download settings:
- 'Select export type' = 'XLS'
- 'Value and header format' = 'XML values and headers'

Expand the 'Advanced options' section and apply the additional settings:
- 'Export *Select Many* questions as...' = 'Single column'
- 'Include fields from all N versions' is **Disabled**. This ensures you will only edit fields that actually exist in the currently deployed form.
- 'Include groups in headers' is **Enabled**, with 'Group separator' = '/'.
- 'Store date and number responses as text' is **Enabled**.
- 'Include media URLs' is **Disabled**.
- 'Select questions to be exported' is **Disabled**. That is, *all* fields are selected for export.
  
Then **Export** your dataset from KoboToolbox. After exporting, load the resulting XLSX file into your favorite spreadsheet application and make your changes. But do not touch the `_uuid` or `meta/rootUuid` columns (or indeed any of the underscore-prefixed fields). If, however, you are using the tool to upload entirely *new* submissions from an existing XLSX spreadsheet - for example, an XLSX exported from another product such (eg Ona) - then you must manually remove any `_uuid` or `meta/rootUuid` column before running the tool, otherwise it will attempt to find existing submissions in your Kobo project that have these uuids (to replace) and thus fail.

**IMPORTANT** - REMOVE ANY ROWS (IE SUBMISSIONS) THAT YOU DO ***NOT*** WANT TO UPDATE. Otherwise, *all* rows - ie all the original exported submissions - will be *re*submitted as an update of the existing submission, even when all the fields remain unchanged. The tool itself cannot determine what has/not been modified in the XLSX so it will attempt to (re)submit everything.

Then cd to the `kobo-transfer-xls` directory and run the command:
[TODO: this script must presently be run from the root dir due to location of .log file. Fix this]

`python3 run.py -N -xt -ef /path/to/my/download.xlsx`

- **-N**  skip `config.json` validation step. This can cause spurious 502 failures
- **-xt**  Excel transfer (read submission data from an Excel file)
- **-ef**  Excel file path [TODO: having both -xt and -ef is redundant so just keep one. Fix this]

# What if it fails?
When any submission(s) fails to update, if you immediately re-run the script it will now reliably fail on any of the previously *successfully* updated submissions. This is because the submission UUID has now been changed for any *successful* updates, so you are basically attempting to edit a submission ID that no longer exists. So instead of blindly rerunning the script and hoping it might magically work, look at the output to identify exactly which submissions failed and note their original UUID; ie "... (was XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX)". Then remove everything *else* from the XLS file except for these failed submission UUIDs. This will ensure that next time you run the tool it wont try to update submissions that were already successful (which now have a brand new UUID). This is, running this script is not idempotent! For the failed updates that remain in the XLS file, the corresponding original submission will be unchanged back in Kobo. You will need to figure out why each didn't update and then try to rerun the script with just the previous failures. Keep removing any *successful* submission UUIDs from the XLS until everything has been successfully updated.

# Debugging
To view the new submission XML, edit `kobo-transfer-xls/transfer/xml.py` and uncomment the relevant section in `def transfer_submissions()`. This is commented out by default because it can generate a huge volume of output for a project with lots of submissions.

# Caveats
Tested successfully on forms with multi nested groups as well as repeats. Tested successfully with edited dates, datetimes and times. Tested successfully with new attachments (eg images), provided these are all put into appropriately named submission-specific subdirs. (see https://github.com/tiritea/kobo-transfer-xls/tree/main/xls_transfer#media-upload). Also confirmed that any pre-existing images from the original submission that are already in Kobo will be preserved and remain attached to the updated submission.

This tool should still be considered pre-release so use at your own risk. Please make sure you retain a backup of the original data (eg backup the original XLSX export file before attempting to edit anything). I also recommend only exporting a couple of submissions to initially edit, check they both update successfully, and then double-check your changes are reflected correctly back in your Kobo project table. Only then try to run it against a larger or entire dataset.

For a large number of submissions, the tool can take a while to re-submit them all one at a time. Although there is some retry logic to handle intermittent 502/503 server response errors due to timeouts, if connectivity to the Kobo server is lost for a period of time then those submissions in-flight will fail (but the tool will move on and continue to try to submit the remaining submissions...). You'll then need to scrub the XLSX of any successful submission and rerun the tool, as described above.

# Special Case: migrating projects from Ona
Although this tool is primarily designed to edit existing Kobo submissions directly from an XLSX export, or create new Kobo submissions from an equivalent Kobo XLSX file, it can also be used to migrate submissions from Ona into Kobo because Ona has an almost identical XLSX export format. There are a few important differences and nuances, however, that need to be taken into consideration when using the tool to migrate an existing Ona project into an equivalent new Kobo project.

First, you will need to download the XLSForm for the Ona project, along with any associated form media, to create an equivalent new project in Kobo using the same form. Although Ona and Kobo both use XLSForms there a some differences. Specifically, strictly speaking XLSForms - and Ona - permit multi questions and groups to share the same name (under certain circumstances...), whereas in Kobo all questions and groups must have a unique name. If you try to upload and deploy a new XLSForm into Kobo that has duplicate names it will fail; you must first edit your form to ensure all questions, groups, calculations, etc have a unique name. And because Ona will export the submission data using the original (ie duplicate) names in the resulting XLSX data export, you will also have to manually rename any columns in the XLSX export to match any name changes you had to make in the XLSForm.

After successfully redeploying your Ona form as a new Kobo project, you then need to export all the submission data out of your Ona project as an Excel file (much as you do when downloading an XLS from Kobo). It is critical to use the correct export settings for this; specifically, *disable* the 'Split select multiple answers into separate columns' and 'Include links of images' options:

<img width="580" height="792" alt="Screenshot 2026-09-15 at 1 10 32 PM" src="https://github.com/user-attachments/assets/0aa4df35-bf2b-4905-9121-6c9a6ac30c3d" />

Then in the resulting XLSX file you must manually remove the **_uuid** and **meta/instanceID** columns. This is because the (Ona) XLSX spreadsheet file will be used to create entirely *new* submissions in Kobo, so there will be no existing submissions in Kobo with these UUIDs. Removing these two columns will trigger the tool to generate *new* submissions with *new* UUIDs (rather than attempting to find existing submissions to replace with your changes, which would necessarily fail). There are also other additional Ona-specific columns - such a **_xform_id**, **_last_edited_by**, **_duration** and **_version** - but the tool is already configured to ignore these.

After removing the **_uuid** and **meta/instanceID** columns - and configuring kobo-transfer-xls/config.json with your Kobo account info - you can then run the tool as normal to generate new submissions, this time from the Ona-generated XLSX file.
