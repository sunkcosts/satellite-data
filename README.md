# Satellite Data

This is a script for collecting satellite data (including elevation data) for this project.

## Dependencies

You will need to get a free [mapbox](https://www.mapbox.com/) API key. The script expects there is a raw text `token` file containing the mapbox API key in the root directory.


## Usage

Clone the repository

```bash
git clone git@github.com:sunkcosts/satellite-data.git
cd satellite-data
pip install -r requirements.txt
```

Run the download script.

```bash
python download.py
```