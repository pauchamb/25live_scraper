"""
25Live Reservation Scraper

This module provides a simple interface for scraping reservation data from the 25Live API.
It fetches reservations within a specified date range and processes them into a structured format.

Requirements:
- API_BASE_URL: The base URL for your 25Live API
- API_USERNAME: Your 25Live API username
- API_PASSWORD: Your 25Live API password

Usage:
    python -m collegenet
"""

import os
import time
import requests
import xmltodict
from datetime import datetime
from typing import List, Dict, Optional, Union
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth


class ReservationScraper:
    """
    A scraper for fetching reservation data from the 25Live API.
    
    This class handles authentication, pagination, and data parsing
    to provide a clean interface for retrieving reservation information.
    """
    
    def __init__(self) -> None:
        """Initialize the reservation scraper with API credentials."""
        # Load environment variables from .env file
        load_dotenv()
        
        # Configuration
        self.PAGE_SIZE = 500
        self.BASE_URL = os.getenv("API_BASE_URL")
        self.username = os.getenv("API_USERNAME")
        self.password = os.getenv("API_PASSWORD")
        
        # Validate required environment variables
        if not self.BASE_URL:
            raise ValueError("API_BASE_URL environment variable is required")
        
        if not self.username or not self.password:
            raise ValueError("API_USERNAME and API_PASSWORD environment variables are required")
        
        # Set up authenticated session
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.username, self.password)

    def _make_api_request(self, url: str) -> Dict:
        """
        Make an authenticated request to the 25Live API.
        
        Args:
            url: The API endpoint URL to request
            
        Returns:
            Parsed XML response as a dictionary
            
        Raises:
            Exception: If the API request fails
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()  # Raises an HTTPError for bad responses
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to make request to {url}: {e}")
        
        try:
            # Parse XML response and extract reservations
            parsed_response = xmltodict.parse(response.text)
            return parsed_response.get("r25:reservations", {})
        except Exception as e:
            raise Exception(f"Failed to parse XML response: {e}")

    def _parse_reservation_data(self, raw_reservations: List[Dict]) -> List[Dict]:
        """
        Parse raw reservation data into a structured format.
        
        Args:
            raw_reservations: List of raw reservation dictionaries from API
            
        Returns:
            List of processed reservation dictionaries
        """
        processed_reservations = []
        
        for reservation in raw_reservations:
            processed_reservation = self._process_single_reservation(reservation)
            processed_reservations.append(processed_reservation)
            
        return processed_reservations

    def _process_single_reservation(self, reservation: Dict) -> Dict:
        """
        Process a single reservation into a structured format.
        
        Args:
            reservation: Raw reservation dictionary from API
            
        Returns:
            Processed reservation dictionary with standardized fields
        """
        # Extract basic reservation information
        processed = {
            "reservation_id": reservation.get("r25:reservation_id"),
            "event_type": reservation.get("r25:event_type_name"),
            "event_id": self._extract_event_id(reservation),
            "reservation_state": reservation.get("r25:reservation_state_name"),
            "reservation_id_friendly": reservation.get("r25:event_locator"),
            "expected_attendance": reservation.get("r25:expected_count"),
            "start": reservation.get("r25:reservation_start_dt"),
            "end": reservation.get("r25:reservation_end_dt"),
            "organization": reservation.get("r25:organization_name"),
        }
        
        # Process event name and title
        processed["name"] = self._combine_event_name_and_title(reservation)
        
        # Add timestamps and friendly date formats
        self._add_datetime_fields(processed, reservation)
        
        # Process location information
        self._add_location_fields(processed, reservation)
        
        return processed

    def _extract_event_id(self, reservation: Dict) -> Optional[str]:
        """Extract event ID from reservation data."""
        event_id = reservation.get("r25:event_id", {})
        if isinstance(event_id, dict):
            return event_id.get("#text")
        return event_id

    def _combine_event_name_and_title(self, reservation: Dict) -> Optional[str]:
        """Combine event name and title into a single descriptive string."""
        name = reservation.get("r25:event_name")
        title = reservation.get("r25:event_title")
        
        if name and title:
            return f"{name} - {title}"
        return name or title

    def _add_datetime_fields(self, processed: Dict, reservation: Dict) -> None:
        """Add timestamp and friendly datetime fields to processed reservation."""
        try:
            # Parse start and end times
            start_time = datetime.fromisoformat(processed["start"])
            end_time = datetime.fromisoformat(processed["end"])
            
            # Add timestamps
            processed["start_timestamp"] = int(start_time.timestamp())
            processed["end_timestamp"] = int(end_time.timestamp())
            
            # Add friendly date strings
            processed["start_date_friendly"] = start_time.strftime("%m/%d/%Y %I:%M %p")
            processed["end_date_friendly"] = end_time.strftime("%m/%d/%Y %I:%M %p")
            
            # Add last updated information
            last_modified = reservation.get("r25:last_mod_dt")
            if last_modified:
                last_mod_time = datetime.fromisoformat(last_modified)
                processed["last_updated_friendly"] = last_mod_time.strftime("%m/%d/%Y %I:%M %p")
                processed["last_updated_timestamp"] = int(last_mod_time.timestamp())
                
        except (ValueError, TypeError) as e:
            print(f"Warning: Could not parse datetime fields: {e}")

    def _add_location_fields(self, processed: Dict, reservation: Dict) -> None:
        """Add location information to processed reservation."""
        space_reservations = reservation.get("r25:space_reservation")
        
        if not space_reservations:
            processed["location_full"] = "Not Specified"
            processed["location_abbr"] = "Not Specified"
            return
        
        # Handle multiple space reservations
        if isinstance(space_reservations, list):
            full_names = []
            abbr_names = []
            
            for space in space_reservations:
                full_name = space.get("r25:formal_name", "").replace(",", "")
                abbr_name = space.get("r25:space_name", "").replace(",", "")
                
                if full_name:
                    full_names.append(full_name)
                if abbr_name:
                    abbr_names.append(abbr_name)
            
            processed["location_full"] = ", ".join(full_names)
            processed["location_abbr"] = ", ".join(abbr_names)
            
        # Handle single space reservation
        elif isinstance(space_reservations, dict):
            processed["location_full"] = space_reservations.get("r25:formal_name", "Not Specified")
            processed["location_abbr"] = space_reservations.get("r25:space_name", "Not Specified")

    def _filter_reservations_by_type(self, reservations: List[Dict]) -> List[Dict]:
        """
        Filter reservations to only include those with 'BL' or 'IN' in event type.
        
        Args:
            reservations: List of reservation dictionaries
            
        Returns:
            Filtered list of reservations
        """
        filtered_reservations = []
        
        for reservation in reservations:
            event_type = reservation.get("event_type", "")
            if "BL" in event_type or "IN" in event_type:
                filtered_reservations.append(reservation)
                
        return filtered_reservations

    def scrape_reservations(self, lookback: str = "-0", lookahead: str = "+0") -> List[Dict]:
        """
        Scrape reservations from the 25Live API within a date range.
        
        Args:
            lookback: Start date offset (e.g., "-7" for 7 days ago, "+0" for today)
            lookahead: End date offset (e.g., "+7" for 7 days from now)
            
        Returns:
            List of processed reservation dictionaries
            
        Example:
            # Get reservations for the next 7 days
            reservations = scraper.scrape_reservations(lookback="+0", lookahead="+7")
        """
        all_reservations = []
        
        # Build initial request URL
        url = self._build_reservations_url(lookback, lookahead, page=1)
        
        # Get first page of results
        response = self._make_api_request(url)
        
        # Check if we have any reservations
        if not response or "r25:reservation" not in response:
            print("No reservations found for the specified date range.")
            return []
        
        # Process first page
        reservations = response["r25:reservation"]
        if not isinstance(reservations, list):
            reservations = [reservations]  # Handle single reservation
            
        all_reservations.extend(self._parse_reservation_data(reservations))
        
        # Handle pagination if there are multiple pages
        page_count = int(response.get("@page_count", "1"))
        
        if page_count > 1:
            print(f"Found {page_count} pages of results. Fetching remaining pages...")
            paginate_key = response["@paginate_key"]
            
            for page_num in range(2, page_count + 1):
                url = self._build_reservations_url(
                    lookback, lookahead, page=page_num, paginate_key=paginate_key
                )
                
                response = self._make_api_request(url)
                reservations = response["r25:reservation"]
                
                if not isinstance(reservations, list):
                    reservations = [reservations]
                    
                all_reservations.extend(self._parse_reservation_data(reservations))
        
        # Filter reservations by event type
        filtered_reservations = self._filter_reservations_by_type(all_reservations)
        
        return filtered_reservations

    def _build_reservations_url(self, lookback: str, lookahead: str, page: int = 1, 
                               paginate_key: Optional[str] = None) -> str:
        """
        Build the URL for fetching reservations.
        
        Args:
            lookback: Start date offset
            lookahead: End date offset
            page: Page number for pagination
            paginate_key: Pagination key from previous response
            
        Returns:
            Complete URL for the API request
        """
        url = f"{self.BASE_URL}/reservations.xml"
        url += f"?start_dt={lookback}&end_dt={lookahead}"
        url += f"&paginate&page_size={self.PAGE_SIZE}"
        
        if page > 1 and paginate_key:
            url += f"&paginate={paginate_key}&page={page}"
            
        return url


class Scraper:
    """
    Main scraper class that orchestrates the reservation fetching process.
    
    This class provides a simple interface for running the scraper across
    multiple date ranges and handling errors gracefully.
    """
    
    def __init__(self):
        """Initialize the scraper with a ReservationScraper instance."""
        self.reservation_scraper = ReservationScraper()

    def run(self, days_ahead: int = 14, step_size: int = 7) -> None:
        """
        Run the scraper across multiple date ranges.
        
        Args:
            days_ahead: Total number of days to scrape ahead
            step_size: Number of days to process in each batch
            
        Example:
            # Scrape the next 30 days in batches of 7 days
            scraper = Scraper()
            scraper.run(days_ahead=30, step_size=7)
        """
        print(f"Starting scrape for the next {days_ahead} days in {step_size}-day batches")
        
        start_time = time.time()
        total_reservations = 0
        
        for day_offset in range(0, days_ahead, step_size):
            try:
                lookback = f"+{day_offset}"
                lookahead = f"+{day_offset + step_size - 1}"
                
                print(f"Scraping days {lookback} to {lookahead}...")
                
                reservations = self.reservation_scraper.scrape_reservations(
                    lookback=lookback, lookahead=lookahead
                )
                
                if reservations:
                    reservation_count = len(reservations)
                    total_reservations += reservation_count
                    print(f"  Found {reservation_count} reservations")
                else:
                    print("  No reservations found")
                    
            except Exception as e:
                print(f"  Error scraping days {lookback} to {lookahead}: {e}")
                continue
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\nScraping completed!")
        print(f"Total reservations found: {total_reservations}")
        print(f"Total time: {duration:.2f} seconds")


if __name__ == "__main__":
    # Example usage
    scraper = Scraper()
    scraper.run()
