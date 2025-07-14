# 25Live Reservation Scraper

A Python scraper for fetching reservation data from the 25Live API. This tool processes reservation data into a structured format and handles pagination automatically.

## Features

- **Authentication**: Secure API authentication using HTTP Basic Auth
- **Pagination**: Automatically handles API pagination to fetch all results
- **Data Processing**: Converts raw XML responses into structured Python dictionaries
- **Error Handling**: Graceful error handling with descriptive messages
- **Type Filtering**: Filters reservations by event type (only includes 'BL' or 'IN' events)
- **Date Formatting**: Provides both timestamps and human-readable date formats

## Setup

### Prerequisites

- Python 3.7+
- Required packages: `requests`, `xmltodict`, `python-dotenv`

### Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install requests xmltodict python-dotenv
   ```

3. Create a `.env` file in the root directory with your API credentials:
   ```env
   API_BASE_URL=https://your-25live-domain.com/25live/ws
   API_USERNAME=your_api_username
   API_PASSWORD=your_api_password
   ```

## Usage

### Basic Usage

```python
from collegenet import ReservationScraper

# Initialize the scraper
scraper = ReservationScraper()

# Get reservations for the next 7 days
reservations = scraper.scrape_reservations(lookback="+0", lookahead="+7")

# Print results
for reservation in reservations:
    print(f"Event: {reservation['name']}")
    print(f"Location: {reservation['location_full']}")
    print(f"Time: {reservation['start_date_friendly']} - {reservation['end_date_friendly']}")
    print("---")
```

### Advanced Usage

```python
# Get reservations from 7 days ago to 14 days from now
reservations = scraper.scrape_reservations(lookback="-7", lookahead="+14")

# Get reservations for a specific day (e.g., 5 days from now)
reservations = scraper.scrape_reservations(lookback="+5", lookahead="+5")
```

### Using the Main Scraper Class

```python
from collegenet import Scraper

# Initialize and run the scraper
scraper = Scraper()

# Scrape the next 30 days in 7-day batches
scraper.run(days_ahead=30, step_size=7)
```

### Command Line Usage

```bash
# Run the scraper with default settings (next 14 days)
python -m collegenet

# Or run the script directly
python collegenet/__main__.py
```

## Data Structure

Each reservation dictionary contains the following fields:

```python
{
    # Basic Information
    "reservation_id": "123456",
    "event_id": "789012",
    "reservation_id_friendly": "EVENT-2024-001",
    "name": "Meeting - Weekly Team Standup",
    "event_type": "BL Academic",
    "reservation_state": "Confirmed",
    "organization": "Computer Science Department",
    "expected_attendance": 25,
    
    # Location Information
    "location_full": "Smith Hall Room 101",
    "location_abbr": "SH 101",
    
    # Date/Time Information (ISO format)
    "start": "2024-01-15T09:00:00",
    "end": "2024-01-15T10:30:00",
    
    # Timestamps (Unix timestamps)
    "start_timestamp": 1705312800,
    "end_timestamp": 1705318200,
    
    # Human-readable dates
    "start_date_friendly": "01/15/2024 09:00 AM",
    "end_date_friendly": "01/15/2024 10:30 AM",
    "last_updated_friendly": "01/10/2024 02:30 PM",
    "last_updated_timestamp": 1704902200
}
```

## API Date Parameters

The scraper uses relative date offsets:

- `lookback="-7"`: 7 days ago
- `lookback="+0"`: Today (default)
- `lookahead="+7"`: 7 days from now
- `lookahead="+14"`: 14 days from now

## Error Handling

The scraper includes comprehensive error handling:

- **Missing credentials**: Validates environment variables on startup
- **API failures**: Handles network errors and invalid responses
- **Data parsing errors**: Gracefully handles malformed XML or missing fields
- **Date parsing errors**: Continues processing if date fields are invalid

## Filtering

The scraper automatically filters reservations to only include events where the event type contains:
- "BL" (typically Building/Location events)
- "IN" (typically Instruction events)

This can be modified in the `_filter_reservations_by_type` method.

## Pagination

The scraper automatically handles pagination:
- Fetches up to 500 reservations per page (configurable)
- Automatically detects and processes multiple pages
- Provides progress feedback for large result sets

## Customization

### Changing Page Size

```python
scraper = ReservationScraper()
scraper.PAGE_SIZE = 100  # Fetch 100 reservations per page
```

### Modifying Event Type Filters

Edit the `_filter_reservations_by_type` method to change which event types are included:

```python
def _filter_reservations_by_type(self, reservations):
    filtered_reservations = []
    for reservation in reservations:
        event_type = reservation.get("event_type", "")
        # Add your custom filtering logic here
        if "YOUR_FILTER" in event_type:
            filtered_reservations.append(reservation)
    return filtered_reservations
```

## Common Use Cases

### 1. Daily Monitoring Script

```python
from collegenet import ReservationScraper

def daily_reservations():
    scraper = ReservationScraper()
    reservations = scraper.scrape_reservations(lookback="+0", lookahead="+1")
    
    print(f"Found {len(reservations)} reservations for today and tomorrow")
    for res in reservations:
        print(f"- {res['name']} at {res['location_abbr']} ({res['start_date_friendly']})")

if __name__ == "__main__":
    daily_reservations()
```

### 2. Export to CSV

```python
import csv
from collegenet import ReservationScraper

def export_to_csv():
    scraper = ReservationScraper()
    reservations = scraper.scrape_reservations(lookback="+0", lookahead="+30")
    
    with open('reservations.csv', 'w', newline='') as csvfile:
        fieldnames = ['name', 'location_full', 'start_date_friendly', 'end_date_friendly', 'organization']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for reservation in reservations:
            writer.writerow({key: reservation.get(key, '') for key in fieldnames})

if __name__ == "__main__":
    export_to_csv()
```

### 3. Weekly Report

```python
from collegenet import ReservationScraper
from collections import defaultdict

def weekly_report():
    scraper = ReservationScraper()
    reservations = scraper.scrape_reservations(lookback="+0", lookahead="+7")
    
    # Group by organization
    by_org = defaultdict(list)
    for res in reservations:
        by_org[res['organization']].append(res)
    
    print("Weekly Reservation Report")
    print("=" * 40)
    
    for org, res_list in by_org.items():
        print(f"\n{org}: {len(res_list)} reservations")
        for res in res_list[:5]:  # Show first 5
            print(f"  - {res['name']} ({res['start_date_friendly']})")

if __name__ == "__main__":
    weekly_report()
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify your credentials in the `.env` file
2. **Network Timeouts**: The scraper will retry failed requests
3. **No Results**: Check your date range parameters
4. **Missing Data**: Some fields may be empty depending on how events are configured in 25Live

### Debug Mode

To see detailed API responses, you can modify the `_make_api_request` method to print the raw XML:

```python
def _make_api_request(self, url: str) -> Dict:
    response = self.session.get(url)
    print(f"API Response: {response.text}")  # Debug line
    # ... rest of method
```

## Contributing

To extend functionality:

1. **Add new data fields**: Modify the `_process_single_reservation` method
2. **Change filtering logic**: Update the `_filter_reservations_by_type` method
3. **Add new output formats**: Create new methods in the `Scraper` class
4. **Improve error handling**: Add more specific exception handling
