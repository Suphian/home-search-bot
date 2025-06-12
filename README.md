# Home Search Bot

This project automates the search for homes in the Dallas-Fort Worth area using Python. It combines real estate APIs with location data to help buyers find homes that meet strict criteria, such as:

- Within a selected city or zip code
- In a top-rated school district
- At least 3-4 bedrooms, 2.5 baths, and 2,000+ sq ft
- Built in the last 20 years
- At least 15% below median price for the area
- Located within:
  - 15 minutes of a Costco
  - 10 minutes of a Target
  - 10 minutes of a mosque
  - 15 minutes of a premium gym (e.g., Life Time, Equinox)
- In a neighborhood with 2–5% annual price appreciation

The script pulls live data, checks all criteria, and outputs a list of matching homes.

## Requirements

- Python 3.7+
- API keys for Google Places, GreatSchools, and a property listing service (see setup instructions)
- Packages: `requests`, `pandas`, `geopy`, `googlemaps`

## Getting Started

1. Clone this repository
2. Add your API keys to a `.env` file (see `.env.example`)
3. Run the main script

## License

MIT
