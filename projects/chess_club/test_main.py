"""
Test suite for Chess Club Event Scheduler
"""
import unittest
from datetime import datetime, timedelta
import os
import sys
import json

# Add the parent directory to the path to import main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import ChessClub, Event, Resource


class TestResource(unittest.TestCase):
    """Test Resource class"""
    
    def test_resource_creation(self):
        """Test basic resource creation"""
        resource = Resource("board_1", "Board 1", "board")
        self.assertEqual(resource.id, "board_1")
        self.assertEqual(resource.name, "Board 1")
        self.assertEqual(resource.type, "board")
        self.assertTrue(resource.available)
    
    def test_resource_with_availability(self):
        """Test resource with availability flag"""
        resource = Resource("board_2", "Board 2", "board", available=False)
        self.assertFalse(resource.available)


class TestEvent(unittest.TestCase):
    """Test Event class"""
    
    def test_event_creation(self):
        """Test basic event creation"""
        start = datetime(2026, 6, 15, 10, 0)
        end = datetime(2026, 6, 15, 12, 0)
        event = Event("ev1", "Test Event", "tournament", start, end)
        
        self.assertEqual(event.id, "ev1")
        self.assertEqual(event.name, "Test Event")
        self.assertEqual(event.type, "tournament")
        self.assertEqual(event.start, start)
        self.assertEqual(event.end, end)
        self.assertEqual(len(event.resources), 0)
        self.assertEqual(event.state, "scheduled")
    
    def test_add_resource(self):
        """Test adding resources to event"""
        event = Event("ev1", "Test", "class", datetime.now(), datetime.now() + timedelta(hours=1))
        resource = Resource("board_1", "Board 1", "board")
        event.add_resource(resource)
        
        self.assertEqual(len(event.resources), 1)
        self.assertEqual(event.resources[0].id, "board_1")
    
    def test_to_dict(self):
        """Test event serialization"""
        start = datetime(2026, 6, 15, 10, 0)
        end = datetime(2026, 6, 15, 12, 0)
        event = Event("ev1", "Test", "tournament", start, end)
        resource = Resource("board_1", "Board 1", "board")
        event.add_resource(resource)
        
        event_dict = event.to_dict()
        self.assertEqual(event_dict["id"], "ev1")
        self.assertEqual(event_dict["name"], "Test")
        self.assertEqual(event_dict["type"], "tournament")
        self.assertEqual(event_dict["resources"], ["board_1"])
        self.assertEqual(event_dict["state"], "scheduled")


class TestChessClub(unittest.TestCase):
    """Test ChessClub class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.club = ChessClub()
        # Add some test resources
        self.club.resources = [
            Resource("board_1", "Board 1", "board"),
            Resource("board_2", "Board 2", "board"),
            Resource("pieces_1", "Pieces 1", "equipment"),
            Resource("clock_1", "Clock 1", "equipment"),
            Resource("arbiter_1", "Arbiter 1", "staff"),
            Resource("fm", "FM Coach", "staff"),
        ]
        self.club.config = {
            "opening_time": "09:00",
            "closing_time": "21:00",
            "min_duration": 0.5,
            "max_duration": 8.0
        }
        self.club.restrictions = [
            {
                "type": "co_requirement",
                "name": "Tournament requires Arbiter",
                "case": "tournament",
                "requires": ["arbiter_1"],
                "min_amount": 1
            },
            {
                "type": "co_requirement",
                "name": "Friendly match requires board and pieces",
                "case": "friendly_match",
                "requires": ["board_1", "board_2", "pieces_1"],
                "min_amount": 2
            },
            {
                "type": "exclusion",
                "name": "Clocks only for tournaments",
                "resources": ["clock_1"],
                "allowed_events": ["tournament"]
            }
        ]
        self.club.event_types = {
            "tournament": {"id": "tournament", "name": "Tournament", "min_duration": 2},
            "friendly_match": {"id": "friendly_match", "name": "Friendly", "min_duration": 0.5},
            "class": {"id": "class", "name": "Class", "min_duration": 1}
        }
    
    def test_search_resource_found(self):
        """Test finding an existing resource"""
        resource = self.club.search_resource("board_1")
        self.assertIsNotNone(resource)
        self.assertEqual(resource.id, "board_1")
    
    def test_search_resource_not_found(self):
        """Test searching for non-existent resource"""
        resource = self.club.search_resource("nonexistent")
        self.assertIsNone(resource)
    
    def test_check_available_no_conflicts(self):
        """Test resource availability with no conflicts"""
        start = datetime(2026, 6, 15, 10, 0)
        end = datetime(2026, 6, 15, 12, 0)
        
        available = self.club.check_available("board_1", start, end)
        self.assertTrue(available)
    
    def test_check_available_with_conflict(self):
        """Test resource availability with conflict"""
        # Schedule an event
        start1 = datetime(2026, 6, 15, 10, 0)
        end1 = datetime(2026, 6, 15, 12, 0)
        event = Event("ev1", "Test", "class", start1, end1)
        resource = self.club.search_resource("board_1")
        event.add_resource(resource)
        self.club.events.append(event)
        
        # Try to check availability for overlapping time
        start2 = datetime(2026, 6, 15, 11, 0)
        end2 = datetime(2026, 6, 15, 13, 0)
        available = self.club.check_available("board_1", start2, end2)
        self.assertFalse(available)
    
    def test_check_available_no_overlap(self):
        """Test resource availability with no overlap"""
        # Schedule an event
        start1 = datetime(2026, 6, 15, 10, 0)
        end1 = datetime(2026, 6, 15, 12, 0)
        event = Event("ev1", "Test", "class", start1, end1)
        resource = self.club.search_resource("board_1")
        event.add_resource(resource)
        self.club.events.append(event)
        
        # Check availability for non-overlapping time
        start2 = datetime(2026, 6, 15, 12, 0)
        end2 = datetime(2026, 6, 15, 14, 0)
        available = self.club.check_available("board_1", start2, end2)
        self.assertTrue(available)
    
    def test_validate_restrictions_co_requirement_pass(self):
        """Test co-requirement validation passes"""
        start = datetime(2026, 6, 15, 10, 0)
        end = datetime(2026, 6, 15, 12, 0)
        event = Event("ev1", "Test Tournament", "tournament", start, end)
        event.add_resource(self.club.search_resource("arbiter_1"))
        
        valid, message = self.club.validate_restrictions(event)
        self.assertTrue(valid)
    
    def test_validate_restrictions_co_requirement_fail(self):
        """Test co-requirement validation fails"""
        start = datetime(2026, 6, 15, 10, 0)
        end = datetime(2026, 6, 15, 12, 0)
        event = Event("ev1", "Test Tournament", "tournament", start, end)
        # Don't add required arbiter
        
        valid, message = self.club.validate_restrictions(event)
        self.assertFalse(valid)
        self.assertIn("tournament", message)
    
    def test_validate_restrictions_exclusion_pass(self):
        """Test exclusion validation passes"""
        start = datetime(2026, 6, 15, 10, 0)
        end = datetime(2026, 6, 15, 12, 0)
        event = Event("ev1", "Test", "tournament", start, end)
        event.add_resource(self.club.search_resource("clock_1"))
        event.add_resource(self.club.search_resource("arbiter_1"))
        
        valid, message = self.club.validate_restrictions(event)
        self.assertTrue(valid)
    
    def test_validate_restrictions_exclusion_fail(self):
        """Test exclusion validation fails"""
        start = datetime(2026, 6, 15, 10, 0)
        end = datetime(2026, 6, 15, 12, 0)
        event = Event("ev1", "Test", "friendly_match", start, end)
        event.add_resource(self.club.search_resource("clock_1"))
        
        valid, message = self.club.validate_restrictions(event)
        self.assertFalse(valid)
    
    def test_schedule_event_success(self):
        """Test successful event scheduling"""
        start = datetime(2026, 6, 15, 10, 0)
        end = datetime(2026, 6, 15, 12, 0)
        
        success, message = self.club.schedule_event(
            "Test Event", "tournament", start, end, ["arbiter_1"]
        )
        
        self.assertTrue(success)
        self.assertEqual(len(self.club.events), 1)
    
    def test_schedule_event_invalid_time(self):
        """Test scheduling with invalid time"""
        start = datetime(2026, 6, 15, 12, 0)
        end = datetime(2026, 6, 15, 10, 0)  # End before start
        
        success, message = self.club.schedule_event(
            "Test", "tournament", start, end, ["arbiter_1"]
        )
        
        self.assertFalse(success)
        self.assertIn("Invalid time", message)
    
    def test_schedule_event_duration_too_short(self):
        """Test scheduling with duration too short"""
        start = datetime(2026, 6, 15, 10, 0)
        end = datetime(2026, 6, 15, 10, 15)  # 0.25 hours
        
        success, message = self.club.schedule_event(
            "Test", "tournament", start, end, ["arbiter_1"]
        )
        
        self.assertFalse(success)
        self.assertIn("Duration", message)
    
    def test_schedule_event_duration_too_long(self):
        """Test scheduling with duration too long"""
        start = datetime(2026, 6, 15, 10, 0)
        end = datetime(2026, 6, 15, 19, 0)  # 9 hours
        
        success, message = self.club.schedule_event(
            "Test", "tournament", start, end, ["arbiter_1"]
        )
        
        self.assertFalse(success)
        self.assertIn("Duration", message)
    
    def test_schedule_event_outside_opening_hours(self):
        """Test scheduling outside club hours"""
        start = datetime(2026, 6, 15, 7, 0)  # Before opening
        end = datetime(2026, 6, 15, 9, 0)
        
        success, message = self.club.schedule_event(
            "Test", "tournament", start, end, ["arbiter_1"]
        )
        
        self.assertFalse(success)
        self.assertIn("club hours", message)
    
    def test_schedule_event_resource_unavailable(self):
        """Test scheduling with unavailable resource"""
        # Schedule first event
        start1 = datetime(2026, 6, 15, 10, 0)
        end1 = datetime(2026, 6, 15, 12, 0)
        self.club.schedule_event("Event 1", "tournament", start1, end1, ["arbiter_1"])
        
        # Try to schedule overlapping event with same resource
        start2 = datetime(2026, 6, 15, 11, 0)
        end2 = datetime(2026, 6, 15, 13, 0)
        success, message = self.club.schedule_event(
            "Event 2", "tournament", start2, end2, ["arbiter_1"]
        )
        
        self.assertFalse(success)
        self.assertIn("not available", message)
    
    def test_schedule_event_fails_co_requirement(self):
        """Test scheduling fails co-requirement"""
        start = datetime(2026, 6, 15, 10, 0)
        end = datetime(2026, 6, 15, 11, 0)
        
        success, message = self.club.schedule_event(
            "Friendly", "friendly_match", start, end, ["board_1"]  # Missing pieces
        )
        
        self.assertFalse(success)
    
    def test_schedule_event_nonexistent_resource(self):
        """Test scheduling with non-existent resource"""
        start = datetime(2026, 6, 15, 10, 0)
        end = datetime(2026, 6, 15, 12, 0)
        
        success, message = self.club.schedule_event(
            "Test", "class", start, end, ["nonexistent_resource"]
        )
        
        self.assertFalse(success)
        self.assertIn("does not exist", message)
    
    def test_delete_event_success(self):
        """Test successful event deletion"""
        start = datetime(2026, 6, 15, 10, 0)
        end = datetime(2026, 6, 15, 12, 0)
        self.club.schedule_event("Test", "tournament", start, end, ["arbiter_1"])
        
        event_id = self.club.events[0].id
        result = self.club.delete_event(event_id)
        
        self.assertTrue(result)
        self.assertEqual(len(self.club.events), 0)
    
    def test_delete_event_not_found(self):
        """Test deleting non-existent event"""
        result = self.club.delete_event("nonexistent")
        self.assertFalse(result)
    
    def test_find_next_slot_available(self):
        """Test finding next available slot"""
        duration = 2.0
        resources = ["board_1", "pieces_1"]
        
        slot = self.club.find_next_slot(duration, resources)
        
        self.assertIsNotNone(slot)
        self.assertGreaterEqual(slot.hour, 9)  # After opening
    
    def test_find_next_slot_with_conflict(self):
        """Test finding slot when resources are occupied"""
        # Schedule event that blocks afternoon slot
        start = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=2)
        self.club.schedule_event("Blocked", "class", start, end, ["board_1"])
        
        # Find slot for board_1
        slot = self.club.find_next_slot(1.0, ["board_1"])
        
        # Should find a slot but not the blocked one
        self.assertIsNotNone(slot)
        if slot.date() == start.date():
            # If same day, should not overlap
            self.assertTrue(slot >= end or slot + timedelta(hours=1) <= start)
    
    def test_find_next_slot_respects_club_hours(self):
        """Test that find_next_slot respects opening hours"""
        duration = 2.0
        resources = ["board_1"]
        
        slot = self.club.find_next_slot(duration, resources)
        
        if slot:
            end_time = slot + timedelta(hours=duration)
            self.assertGreaterEqual(slot.hour, 9)
            self.assertLessEqual(end_time.hour, 21)
    
    def test_find_next_slot_no_midnight_crossing(self):
        """Test that find_next_slot doesn't return slots that cross midnight"""
        duration = 8.0  # Long duration
        resources = ["board_1"]
        
        slot = self.club.find_next_slot(duration, resources)
        
        if slot:
            end_time = slot + timedelta(hours=duration)
            # Should be on the same day
            self.assertEqual(slot.date(), end_time.date())


class TestChessClubFileOperations(unittest.TestCase):
    """Test file save/load operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.club = ChessClub()
        self.club.resources = [
            Resource("board_1", "Board 1", "board"),
            Resource("arbiter_1", "Arbiter 1", "staff"),
        ]
        self.club.config = {
            "opening_time": "09:00",
            "closing_time": "21:00",
            "min_duration": 0.5,
            "max_duration": 8.0
        }
        self.club.restrictions = []
        self.test_file = "/tmp/test_chess_club.json"
    
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
    
    def test_save_and_load_events(self):
        """Test saving and loading events"""
        # Create an event
        start = datetime(2026, 6, 15, 10, 0)
        end = datetime(2026, 6, 15, 12, 0)
        event = Event("ev1", "Test Event", "tournament", start, end)
        event.add_resource(self.club.search_resource("board_1"))
        self.club.events.append(event)
        
        # Save
        self.club.save_file(self.test_file)
        
        # Load into new club
        new_club = ChessClub()
        new_club.resources = self.club.resources
        new_club.load_file(self.test_file)
        
        # Verify
        self.assertEqual(len(new_club.events), 1)
        self.assertEqual(new_club.events[0].name, "Test Event")
        self.assertEqual(new_club.events[0].type, "tournament")
    
    def test_save_empty_events(self):
        """Test saving with no events"""
        self.club.save_file(self.test_file)
        
        # Check file exists and has empty events
        with open(self.test_file, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data["events"], [])
    
    def test_load_nonexistent_file(self):
        """Test loading non-existent file doesn't crash"""
        self.club.load_file("/tmp/nonexistent_file.json")
        # Should not raise exception


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.club = ChessClub()
        self.club.resources = [
            Resource("board_1", "Board 1", "board"),
        ]
        self.club.config = {
            "min_duration": 0.5,
            "max_duration": 8.0
        }
        self.club.restrictions = []
        self.club.event_types = {}
    
    def test_schedule_event_exact_min_duration(self):
        """Test scheduling with exact minimum duration"""
        start = datetime(2026, 6, 15, 10, 0)
        end = start + timedelta(hours=0.5)
        
        success, _ = self.club.schedule_event(
            "Test", "class", start, end, ["board_1"]
        )
        
        self.assertTrue(success)
    
    def test_schedule_event_exact_max_duration(self):
        """Test scheduling with exact maximum duration"""
        start = datetime(2026, 6, 15, 10, 0)
        end = start + timedelta(hours=8.0)
        
        success, _ = self.club.schedule_event(
            "Test", "class", start, end, ["board_1"]
        )
        
        self.assertTrue(success)
    
    def test_schedule_event_empty_resources(self):
        """Test scheduling with no resources"""
        start = datetime(2026, 6, 15, 10, 0)
        end = datetime(2026, 6, 15, 12, 0)
        
        success, _ = self.club.schedule_event(
            "Test", "class", start, end, []
        )
        
        # Should succeed if no co-requirements
        self.assertTrue(success)
    
    def test_check_available_nonexistent_resource(self):
        """Test checking availability of non-existent resource"""
        start = datetime(2026, 6, 15, 10, 0)
        end = datetime(2026, 6, 15, 12, 0)
        
        available = self.club.check_available("nonexistent", start, end)
        self.assertFalse(available)
    
    def test_schedule_without_opening_hours_config(self):
        """Test scheduling when opening hours not configured"""
        # Don't set opening_time and closing_time
        start = datetime(2026, 6, 15, 10, 0)
        end = datetime(2026, 6, 15, 12, 0)
        
        success, _ = self.club.schedule_event(
            "Test", "class", start, end, ["board_1"]
        )
        
        # Should succeed without time validation
        self.assertTrue(success)


if __name__ == '__main__':
    unittest.main()
