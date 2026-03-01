Export submissions from your Kobo project's DATA tab with Downloads settings:
- 'Select export type' = 'XLS'
- 'Value and header format' = 'XML values and headers'

Expand the 'Advanced options' section and apply the addition settings:
- 'Export *Select Many* questions as...' = 'Single column'
- 'Include fields from all N versions' is **Enabled**.
- 'Include groups in headers' is **Enabled**, with 'Group separator' = '/'.
- 'Store date and number responses as text' is **Enabled**.
- 'Include media URLs' is **Disabled**.
- 'Select questions to be exported' is **Disabled**. That is, *all* fields are selected for export.
  
Then Export your dataset. After exporting, load the resulting XLSX file into your favorite spreadsheet application and make your changes. But do not touch the `_uuid` or `meta/rootUuid` columns (or, indeed, any of the underscore-prefixed fields).

**IMPORTANT** - REMOVE ANY ROWS (IE SUBMISSIONS) THAT YOU DO ***NOT*** WANT TO UPDATE. Otherwise, *all* rows - ie all the exported submissions - will be *re*submitted as an update of the existing submission, even if all the fields remain unchanged.

Then run:

`python3 run.py -N -xt -ef /path/to/my.xlsx`
