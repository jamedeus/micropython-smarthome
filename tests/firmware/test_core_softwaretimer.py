import time
import asyncio
import unittest
import SoftwareTimer
from cpython_only import cpython_only


class TestSoftwareTimer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()
        cls.loop.create_task(SoftwareTimer.timer.loop())

    def setUp(self):
        # Create dict to track when callback functions ran
        self.callbacks = {}
        self.callbacks['test1'] = {'called': False, 'time': None}
        self.callbacks['test2'] = {'called': False, 'time': None}

        # Ensure no timers from previous test in queue
        SoftwareTimer.timer.cancel('test1')
        SoftwareTimer.timer.cancel('test2')

    # Mock callback function, stores epoch time when called
    def callback1(self):
        self.callbacks['test1']['called'] = True
        self.callbacks['test1']['time'] = time.time()

    # Mock callback function, stores epoch time when called
    def callback2(self):
        self.callbacks['test2']['called'] = True
        self.callbacks['test2']['time'] = time.time()

    # Takes int (milliseconds)
    async def wait(self, delay):
        await asyncio.sleep_ms(delay)

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

    def test_loop(self):
        # Get start epoch time
        start_time = time.time()

        # Create 2 timers expiring in 1 second and 5 seconds respectively
        SoftwareTimer.timer.create(1000, self.callback1, 'test1')
        SoftwareTimer.timer.create(5000, self.callback2, 'test2')

        # Run event loop for 1.1 seconds
        self.loop.run_until_complete(self.wait(1100))

        # Confirm callback1 ran
        self.assertTrue(self.callbacks['test1']['called'])

        # Confirm callback ran within 50ms of expected time
        elapsed_time = self.callbacks['test1']['time'] - start_time
        self.assertTrue(.95 <= elapsed_time <= 1.05)

        # Confirm callback2 was NOT called
        self.assertEqual(self.callbacks['test2']['called'], False)
        self.assertEqual(self.callbacks['test2']['time'], None)

    def test_loop_pauses_when_no_timer_due(self):
        # Get start epoch time
        start_time = time.time()

        # Create timer expiring in 2 seconds
        SoftwareTimer.timer.create(2000, self.callback1, 'test1')

        # Confirm loop not paused
        self.assertFalse(SoftwareTimer.timer.pause)

        # Run event loop for 500ms
        self.loop.run_until_complete(self.wait(500))

        # Confirm callback1 did NOT run
        self.assertFalse(self.callbacks['test1']['called'])

        # Confirm loop is paused (no timer due in next 1000ms)
        self.assertTrue(SoftwareTimer.timer.pause)

        # Run event loop for another 1.6 seconds, confirm callback1 was called
        self.loop.run_until_complete(self.wait(1600))
        self.assertTrue(self.callbacks['test1']['called'])

        # Confirm callback ran within 50ms of expected time
        elapsed_time = self.callbacks['test1']['time'] - start_time
        self.assertTrue(1.95 <= elapsed_time <= 2.05)

    @cpython_only
    def test_empty_loop(self):
        # Clear queue and schedule
        SoftwareTimer.timer.queue = []
        SoftwareTimer.timer.schedule = {}

        # Confirm loop not paused
        self.assertFalse(SoftwareTimer.timer.pause)

        # Run event loop for 100ms (branch coverage for iterating empty queue)
        self.loop.run_until_complete(self.wait(100))

        # Confirm loop paused, created hardware timer to unpause in 1 hour
        self.assertTrue(SoftwareTimer.timer.pause)
        from machine import Timer
        timer = Timer(0)
        self.assertEqual(timer.period, 3600)

    def test_regression_timer_created_in_callback_function_runs_late(self):
        '''Original bug: If SoftwareTimer.create was called by a timer callback
        function (eg DimmableLight.fade), and the new timer expired before all
        existing timers, it would not run until the next timer expired or the
        create/cancel methods were called again.

        SoftwareTimer.loop iterates self.queue, runs callbacks for all expired
        timers until the first non-expired timer is reached, then pauses and
        creates an interrupt to resume when the non-expired timer is due. When
        a callback function creates a new timer it is not added to the queue
        loop is iterating, so the resume interrupt could be scheduled after the
        newly created timer expires. The end of SoftwareTimer.loop also sets
        self.pause to True, undoing the change by SoftwareTimer.create.

        This was originally fixed in 47d0c2e7, but the bug was reintroduced 2
        years later by e8ac9075 due to lack of a regression test or details to
        reproduce the bug. This bug can be reliably reproduced by starting a
        DimmableLight.fade with many steps and a short duration (to ensure new
        timer is first in queue) - the fade will not run until SoftwareTimer is
        unpaused by the resume interrupt (next timer) or the create/cancel
        methods (eg MotionSensor detects motion and creates reset timer).
        '''

        # Create callback function that creates a timer due in 10 ms
        def callback_that_creates_timer():
            SoftwareTimer.timer.create(10, self.callback1, 'test1')

        # Schedule the callback to run immediately
        SoftwareTimer.timer.create(0, callback_that_creates_timer, 'test')

        # Run event loop for 100ms to allow both timers to complete
        self.loop.run_until_complete(self.wait(100))

        # Confirm the timer created by callback ran
        self.assertTrue(self.callbacks['test1']['called'])
