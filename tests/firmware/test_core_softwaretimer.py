import unittest
import SoftwareTimer


class TestSoftwareTimer(unittest.TestCase):

    def test_create(self):
        # Create timer
        SoftwareTimer.timer.create(10000, print, "unit_test")

        # Confirm timer is now in schedule
        count = 0
        for i in SoftwareTimer.timer.schedule:
            if SoftwareTimer.timer.schedule[i][0] == "unit_test":
                count += 1
                timestamp = i

        # Should only have 1 task
        self.assertEqual(count, 1)

        # Confirm same timestamp is also in queue
        for i in SoftwareTimer.timer.queue:
            if timestamp == i:
                self.assertTrue(True)
                break
        else:
            # Only runs if iteration completes without finding a match
            self.assertTrue(False)

    def test_create_duplicate(self):
        # Attempt to create 2 tasks - second should overwrite the first
        SoftwareTimer.timer.create(10000, print, "unit_test")
        SoftwareTimer.timer.create(20000, print, "unit_test")

        # Confirm task is now in queue
        count = 0
        for i in SoftwareTimer.timer.schedule:
            if SoftwareTimer.timer.schedule[i][0] == "unit_test":
                count += 1

        # Should only have 1 task
        self.assertEqual(count, 1)

    def test_cancel(self):
        # Create task to cancel
        SoftwareTimer.timer.create(10000, print, "unit_test")

        # Cancel task
        SoftwareTimer.timer.cancel("unit_test")

        # Confirm task is NOT in queue
        count = 0
        for i in SoftwareTimer.timer.schedule:
            if SoftwareTimer.timer.schedule[i][0] == "unit_test":
                count += 1

        # Should not have found a match
        self.assertEqual(count, 0)

    def test_create_at_same_time(self):
        # Create 2 tasks at same time (different names so they aren't considered duplicates and canceled)
        SoftwareTimer.timer.create(10000, print, "test1")
        SoftwareTimer.timer.create(10000, print, "test2")

        # Find both expiration timestamps
        for i in SoftwareTimer.timer.schedule:
            if SoftwareTimer.timer.schedule[i][0] == "test1":
                test1_expiration = i
            elif SoftwareTimer.timer.schedule[i][0] == "test2":
                test2_expiration = i

        # Second timestamp should be 1 ms later than first
        self.assertEqual((test2_expiration - test1_expiration), 1)
