# MBTA

An e-ink display for upcoming MBTA arrivals.

## Configuration

Configuration is provided via environment variables.
All environment variables are prefixed with `MBTA_`

- `MBTA_APIKEY` provides the API key used to call the MBTA APIs. Get a free key at https://api-v3.mbta.com/.

## Development

Install in editable mode

```sh
pip install -e .
```

### Building

```sh
python3 -m pip install build
python3 -m build
```
