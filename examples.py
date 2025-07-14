#!/usr/bin/env python3
"""
Example usage scripts for the 25Live Reservation Scraper.

This file contains practical examples of how to use the scraper
for common tasks like daily monitoring, reporting, and data export.
"""

import csv
from datetime import datetime
from collections import defaultdict
from collegenet import ReservationScraper


def example_1_basic_usage():
    """
    Example 1: Basic scraping for the next 7 days
    """
    print("=== Example 1: Basic Usage ===")
    
    # Initialize the scraper
    scraper = ReservationScraper()
    
    # Get reservations for the next 7 days
    reservations = scraper.scrape_reservations(lookback="+0", lookahead="+7")
    
    print(f"Found {len(reservations)} reservations for the next 7 days:")
    
    # Display first 5 reservations
    for i, reservation in enumerate(reservations[:5]):
        print(f"\n{i+1}. {reservation['name']}")
        print(f"   Location: {reservation['location_full']}")
        print(f"   Time: {reservation['start_date_friendly']} - {reservation['end_date_friendly']}")
        print(f"   Organization: {reservation['organization']}")
        print(f"   Event Type: {reservation['event_type']}")
    
    if len(reservations) > 5:
        print(f"\n... and {len(reservations) - 5} more reservations")


def example_2_daily_monitoring():
    """
    Example 2: Daily monitoring script for today's events
    """
    print("\n=== Example 2: Today's Events ===")
    
    scraper = ReservationScraper()
    
    # Get only today's reservations
    reservations = scraper.scrape_reservations(lookback="+0", lookahead="+0")
    
    if not reservations:
        print("No reservations found for today.")
        return
    
    print(f"Today's Schedule ({len(reservations)} events):")
    print("-" * 50)
    
    # Sort by start time
    reservations.sort(key=lambda x: x['start_timestamp'])
    
    for reservation in reservations:
        start_time = datetime.fromtimestamp(reservation['start_timestamp'])
        print(f"{start_time.strftime('%I:%M %p')} - {reservation['name']}")
        print(f"  📍 {reservation['location_abbr']}")
        print(f"  👥 {reservation['expected_attendance'] or 'N/A'} expected")
        print()


def example_3_weekly_report():
    """
    Example 3: Generate a weekly report grouped by organization
    """
    print("\n=== Example 3: Weekly Report by Organization ===")
    
    scraper = ReservationScraper()
    
    # Get reservations for the next 7 days
    reservations = scraper.scrape_reservations(lookback="+0", lookahead="+7")
    
    # Group by organization
    by_organization = defaultdict(list)
    for reservation in reservations:
        org = reservation['organization'] or 'Unknown Organization'
        by_organization[org].append(reservation)
    
    print("Weekly Reservation Report")
    print("=" * 60)
    
    total_events = 0
    for org, org_reservations in sorted(by_organization.items()):
        print(f"\n📊 {org}")
        print(f"   {len(org_reservations)} reservations")
        
        # Show most popular locations for this org
        locations = defaultdict(int)
        for res in org_reservations:
            locations[res['location_abbr']] += 1
        
        if locations:
            top_location = max(locations, key=locations.get)
            print(f"   Most used location: {top_location} ({locations[top_location]} times)")
        
        total_events += len(org_reservations)
    
    print(f"\n📈 Total Events: {total_events}")


def example_4_export_to_csv():
    """
    Example 4: Export reservations to CSV file
    """
    print("\n=== Example 4: Export to CSV ===")
    
    scraper = ReservationScraper()
    
    # Get reservations for the next 30 days
    reservations = scraper.scrape_reservations(lookback="+0", lookahead="+30")
    
    if not reservations:
        print("No reservations found to export.")
        return
    
    # Define CSV fields
    fieldnames = [
        'name', 'organization', 'location_full', 'location_abbr',
        'start_date_friendly', 'end_date_friendly', 'expected_attendance',
        'event_type', 'reservation_state'
    ]
    
    filename = f'reservations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for reservation in reservations:
            # Create a row with only the fields we want
            row = {field: reservation.get(field, '') for field in fieldnames}
            writer.writerow(row)
    
    print(f"✅ Exported {len(reservations)} reservations to {filename}")


def example_5_room_utilization():
    """
    Example 5: Analyze room utilization
    """
    print("\n=== Example 5: Room Utilization Analysis ===")
    
    scraper = ReservationScraper()
    
    # Get reservations for the next 14 days
    reservations = scraper.scrape_reservations(lookback="+0", lookahead="+14")
    
    if not reservations:
        print("No reservations found for analysis.")
        return
    
    # Count reservations by room
    room_usage = defaultdict(int)
    room_hours = defaultdict(float)
    
    for reservation in reservations:
        room = reservation['location_abbr']
        room_usage[room] += 1
        
        # Calculate hours (duration in seconds / 3600)
        duration = reservation['end_timestamp'] - reservation['start_timestamp']
        room_hours[room] += duration / 3600
    
    print("Room Utilization (Next 14 Days)")
    print("-" * 40)
    
    # Sort by usage count
    sorted_rooms = sorted(room_usage.items(), key=lambda x: x[1], reverse=True)
    
    for i, (room, count) in enumerate(sorted_rooms[:10]):  # Top 10 rooms
        hours = room_hours[room]
        print(f"{i+1:2d}. {room:20s} - {count:2d} bookings, {hours:5.1f} hours")
    
    if len(sorted_rooms) > 10:
        print(f"    ... and {len(sorted_rooms) - 10} more rooms")


def example_6_search_and_filter():
    """
    Example 6: Search and filter reservations
    """
    print("\n=== Example 6: Search and Filter ===")
    
    scraper = ReservationScraper()
    
    # Get reservations for the next 30 days
    reservations = scraper.scrape_reservations(lookback="+0", lookahead="+30")
    
    if not reservations:
        print("No reservations found for filtering.")
        return
    
    # Example: Find all events with "meeting" in the name
    meeting_events = [
        res for res in reservations 
        if 'meeting' in res['name'].lower()
    ]
    
    print(f"Found {len(meeting_events)} events with 'meeting' in the name:")
    for event in meeting_events[:5]:  # Show first 5
        print(f"  • {event['name']} ({event['start_date_friendly']})")
    
    # Example: Find large events (>50 people)
    large_events = [
        res for res in reservations 
        if res['expected_attendance'] and int(res['expected_attendance']) > 50
    ]
    
    print(f"\nFound {len(large_events)} large events (>50 people):")
    for event in large_events[:5]:  # Show first 5
        print(f"  • {event['name']} - {event['expected_attendance']} people")
    
    # Example: Find events in specific building
    building_filter = "SH"  # Smith Hall
    building_events = [
        res for res in reservations 
        if building_filter in res['location_abbr']
    ]
    
    print(f"\nFound {len(building_events)} events in {building_filter} building:")
    for event in building_events[:5]:  # Show first 5
        print(f"  • {event['name']} in {event['location_abbr']}")


def main():
    """
    Run all examples
    """
    print("25Live Reservation Scraper - Usage Examples")
    print("=" * 60)
    
    try:
        example_1_basic_usage()
        example_2_daily_monitoring()
        example_3_weekly_report()
        example_4_export_to_csv()
        example_5_room_utilization()
        example_6_search_and_filter()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("\nTip: You can run individual examples by calling them directly:")
        print("     python examples.py")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("\nMake sure you have:")
        print("1. Set up your .env file with valid credentials")
        print("2. Installed all required packages")
        print("3. Network connectivity to your 25Live API")


if __name__ == "__main__":
    main() 