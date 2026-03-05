# Setup
Clone this repo to your system with the following command:

  `git clone https://github.com/tiritea/kobo-transfer-xls.git`

Copy the sample config file to customise to your Kobo account:

  `cp kobo-transfer-xls/sample-config.json kobo-transfer-xls/config.json`

There are some additional python environment pre-requisites described in `kobo-transfer-xls/xls_transfer/README.md`

# Configuration
Edit `config.json` with your Kobo project and account settings; add these to *both* the `source` and `dest` JSON settings.
- get `kc_url` from *FORM* -> *Collect data* -> *Android application* (eg https://kc.kobotoolbox.org)
- get `kf_url` from any project page URL prefix (eg https://kf.kobotoolbox.org)
- get the `token` from your *Account* -> *Account settings* - *Security* page. **Display** and then copy the **API Key** value
- get the `asset_uid` from the project summary page URL (eg kf.kobotoolbox.org/#/forms/**a7d7KzP5YJ9d9fhdWyGNtJ**/summary)

# Usage
Export submissions from your Kobo project's DATA tab with the following Download settings:
- 'Select export type' = 'XLS'
- 'Value and header format' = 'XML values and headers'

Expand the 'Advanced options' section and apply the additional settings:
- 'Export *Select Many* questions as...' = 'Single column'
- 'Include fields from all N versions' is **Enabled**.
- 'Include groups in headers' is **Enabled**, with 'Group separator' = '/'.
- 'Store date and number responses as text' is **Enabled**.
- 'Include media URLs' is **Disabled**.
- 'Select questions to be exported' is **Disabled**. That is, *all* fields are selected for export.
  
Then **Export** your dataset. After exporting, load the resulting XLSX file into your favorite spreadsheet application and make your changes. But do not touch the `_uuid` or `meta/rootUuid` columns (or, indeed, any of the underscore-prefixed fields).

**IMPORTANT** - REMOVE ANY ROWS (IE SUBMISSIONS) THAT YOU DO ***NOT*** WANT TO UPDATE. Otherwise, *all* rows - ie all the exported submissions - will be *re*submitted as an update of the existing submission, even if all the fields remain unchanged.

Then cd to the `kobo-transfer-xls` directory and run the command:
[this script must be run from the root dir due to location of .log file. **TODO**: fix this!]

`python3 run.py -N -xt -ef /path/to/my/download.xlsx`

- **-N**  skip `config.json` validation step. This can cause spurious 502 failures
- **-xt**  Excel transfer (read submission data from an Excel file)
- **-ef**  Excel file path [**TODO**: having both -xt and -ef is redundant, just keep one!]

# What if it fails?
When any submission(s) fails to update, if you immediately re-run the script it will now reliably fail on any of the previously *successfully* updated submissions (!). This is because the submission UUID has now been changed for any *successful* updates, so you are basically attempting to edit a submission ID that no longer exists! So instead of blindly rerunning the script and hoping it'll work, look in the output for exactly which submissions failed and note their original UUID; ie "... (was XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX)". Then remove everything from the XLS file *except* these failed submission UUIDs; this ensures that next time you run the script it wont try to update submissions that were already successful and now have a new UUID. This is to say, running this script is not idempotent! For the remaining failed updates in the XLS file, the corresponding original submission will be unchanged back in Kobo. So you'll need to figure out why they didnt update and then try to rerun the script with them. Keep removing any previously successful updates from the XLS until everything has been successfully updated.

# Debugging
To view the new submission XML, edit `kobo-transfer-xls/transfer/xml.py` and uncomment the relevant section in `def transfer_submissions()`

# Caveats
Tested and working with multi nested groups, as well as repeats. Tested with edited dates, datetimes and times (this caused problems before...). Haven't tested adding new attachmetns or images yet, but checked that any pre-existing images on the original submission are preserved and remain attached to the updated submission.
