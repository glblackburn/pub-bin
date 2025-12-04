# greynoise-lookup.sh

A utility script to query the GreyNoise Community API for IP address threat intelligence information.

## Overview

The `greynoise-lookup.sh` script provides a command-line interface to query GreyNoise's Community API, which offers free threat intelligence data about IP addresses without requiring an API key.

## Features

- Queries GreyNoise Community API (no API key required)
- Validates IP address format and octet ranges
- Handles HTTP status codes appropriately (200, 404, 429, 4xx, 5xx)
- Provides clear error messages for different failure scenarios
- Supports quiet and verbose output modes

## Usage

```bash
./greynoise/greynoise-lookup.sh [-hqv] <ip_address>
```

**Options:**
- `-h` : Display help message
- `-q` : Quiet mode (output as little as possible)
- `-v` : Verbose output (shows detailed request information)

**Arguments:**
- `<ip_address>` : IP address to query (required)

## Examples

```bash
# Query Google DNS IP
./greynoise/greynoise-lookup.sh 8.8.8.8

# Verbose mode
./greynoise/greynoise-lookup.sh -v 192.168.1.1

# Quiet mode
./greynoise/greynoise-lookup.sh -q 1.1.1.1
```

## Dependencies

- `curl` - Required for API requests (typically pre-installed on macOS/Linux)

## API Information

- **API URL**: `https://api.greynoise.io/v3/community`
- **Documentation**: https://docs.greynoise.io/docs/using-the-greynoise-community-api
- **Rate Limits**: The Community API has rate limits (HTTP 429 responses)

## Error Handling

The script handles various HTTP status codes:
- **200**: Success - IP data returned
- **404**: IP not found in database (treated as success, informational message)
- **429**: Rate limit exceeded (error)
- **4xx**: Client errors (error)
- **5xx**: Server errors (error)

## Validation

The script validates IP addresses:
- Format: Must match IPv4 dotted decimal notation (e.g., `192.168.1.1`)
- Octets: Each octet must be in range 0-255
- Provides clear error messages for invalid IPs

This script is useful for quickly checking IP addresses against GreyNoise's threat intelligence database to determine if an IP is associated with malicious activity, scanning, or other security concerns.
