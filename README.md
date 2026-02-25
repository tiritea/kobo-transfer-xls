Export submission from Kobo project with settings:
- 'Select export type' = 'XLS'
- 'Value and header format' = 'XML values and headers'
- 'Include fileds from all X versions' is *disabled*
- 'Include groups in headers' is *enabled*, with 'Group separator' = '/'
Then Export your dataset.
After exporting, load the resulting XLSX file and make your changes. **REMOVE ANY ROWS (IE SUBMISSIONS) THAT YOU DO NOT WANT TO UPDATE*, otherwise *all* rows will be resubmitted as edits for their existing submission.
Then run:
    python3 run.py -N -xt -ef /path/to/my.xlsx
