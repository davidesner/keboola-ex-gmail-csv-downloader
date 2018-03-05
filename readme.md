## Gmail zip attachment extractor for KBC
Extractor component for Keboola Connection allowing to retrieve single file attachments in ZIP format and load its' content to Storage based on prefix and other parameters

## Funcionality

Component looks for emails with single attachments and retrieves its content based on specified prefix.

Specify GMAIL lookup [query](https://developers.google.com/gmail/api/guides/filtering) to filter required emails. E.g. `subject:My email w attachment`

Then specify prefix, csv file parameters and sapi path for group of files in the archive that should be merged together. If the file does not contain header, it may be specified explicitly.

### Configuration parameters
- **Gmail search query** – (REQ) Lookup query to filter emails. e.g. `subject:my email` For more details look [here](https://developers.google.com/gmail/api/guides/filtering)
- **GMAIL user name** - username of gmail account. e.g. `mymail@gmail.com` 
- **File compression** – (REQ) Compression type. Currently only `ZIP` supported. 
- **Bucket name** - (REQ) Storage bucket name e.g. `in.c-gmail-ex`
- **Continue since last run** – Flag whether to download only emails that were added since the last run. If set to No all matching files in the repository will be downloaded.
- **Files in archive to download** - (REQ) list of files to download 
    - **Table name** - (REQ) Storage table where the result will be uploaded (e.g. mytable).
    - **Download folder or file** – (DEFAULT FOLDER) indicator whether to
		download a single file or the whole folder 
	 - **Filename prefix** – Prefix string of files in archive to download and group into single table 
    - **File header** - (OPT) File header. If specified, all files with prefix are expected to not contain header. If empty, header in files are expected. Delimiter must match the one specified and the number of columns must match exactly the source file!
    - **Storage upload mode** – (DEFAULT INCREMENTAL) specifies whether
		to upload incrementally. If set to INCREMENTAL, the pkey must be
		specified. 		 
    - **Primary Key** – (REQ) – array of names of the primary key columns, required (If upload mode is INCREMENTAL)
    
    - **Delimiter** – (DEFAULT ,) delimiter remote csv file	(default , ) 
