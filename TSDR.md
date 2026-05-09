# USPTO TSDR API Client

This project provides a Python client for accessing USPTO Trademark Status and Document Retrieval (TSDR) data via their REST API.

## Prerequisites

1. **USPTO Account**: Create an account at [USPTO.gov](https://www.uspto.gov/)
2. **API Key**: Register for an API key at [API Manager](https://account.uspto.gov/api-manager/)
   - The API uses the header `USPTO-API-KEY` for authentication.
   - Follow the [User Guide](https://developer.uspto.gov/files/tsdr-api-key-manager-user-guide) for current instructions.
3. **Python 3.6+**

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your API key as an environment variable:
   ```bash
   export USPTO_API_KEY="your_api_key_here"
   ```

   Or create a `.env` file in the project directory with:
   ```text
   USPTO_API_KEY=your_api_key_here
   ```

   The client now loads `.env` automatically via `python-dotenv`.

## Usage

Run the script:
```bash
python tsdr_client.py
```

This will demonstrate fetching case status and last update for an example serial number.

## API Endpoints

The client supports:
- Getting case status (`/ts/cd/casestatus/{caseid}/info`)
- Getting last update time (`/last-update/info.json`)
- Bulk status for multiple cases (`/ts/cd/caseMultiStatus/{type}`)
- Downloading documents (`/ts/cd/casedoc/{caseid}/{docid}/content.{format}`)

## Rate Limits

- 60 requests per minute per API key
- 4 requests per minute for PDF, ZIP, and multi-case downloads

## Documentation

- [TSDR API Catalog](https://developer.uspto.gov/api-catalog/tsdr-data-api)
- [Swagger Documentation](https://developer.uspto.gov/swagger/tsdr-api-v1)
- [Bulk Download FAQ](https://developer.uspto.gov/faq/tsdr-api-bulk-download)

## Support

For API issues, email [TEAS@uspto.gov](mailto:TEAS@uspto.gov)