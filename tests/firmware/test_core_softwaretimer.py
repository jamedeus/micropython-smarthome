import time
import asyncio
import unittest
import app_context
from cpython_only import cpython_only


class TestSoftwareTimer(unittest.TestCase):

    # Used to yield so SoftwareTimer create/cancel tasks can run
    async def sleep(self, ms):
        await asyncio.sleep_ms(ms)

    def setUp(self):
        # Create dict to track when callback functions ran
        self.callbacks = {}
        self.callbacks['test1'] = {'called': False, 'time': None}
        self.callbacks['test2'] = {'called': False, 'time': None}

        # Ensure no timers from previous test in queue
        app_context.timer_instance.cancel('test1')
        app_context.timer_instance.cancel('test2')
        app_context.timer_instance.cancel('test3')
        app_context.timer_instance.cancel('unit_test')
        # Yield to let cancel coroutine run
        asyncio.run(self.sleep(10))

    # Mock callback function, stores epoch time when called
    def callback1(self):
        self.callbacks['test1']['called'] = True
        self.callbacks['test1']['time'] = time.time()

    # Mock callback function, stores epoch time when called
    def callback2(self):
        self.callbacks['test2']['called'] = True
        self.callbacks['test2']['time'] = time.time()

    def test_create(self):
        # Create timer, yield to let create coroutine run
        app_context.timer_instance.create(10000, print, "unit_test")
        asyncio.run(self.sleep(10))

        # Confirm timer is now in schedule
        count = 0
        for i in app_context.timer_instance.schedule:
            if app_context.timer_instance.schedule[i][0] == "unit_test":
                count += 1
                timestamp = i

        # Should only have 1 task
        self.assertEqual(count, 1)

        # Confirm same timestamp is also in queue
        for i in app_context.timer_instance.queue:
            if timestamp == i:
                self.assertTrue(True)
                break
        else:
            # Only runs if iteration completes without finding a match
            self.assertTrue(False)

    def test_create_duplicate(self):
        # Attempt to create 2 tasks - second should overwrite the first
        app_context.timer_instance.create(10000, print, "unit_test")
        app_context.timer_instance.create(20000, print, "unit_test")
        # Yield to let create coroutine run
        asyncio.run(self.sleep(10))

        # Confirm only 1 task in queue
        rules = [time for time, rule in app_context.timer_instance.schedule.items()
                 if rule[0] == "unit_test"]
        self.assertEqual(len(rules), 1)

    def test_cancel(self):
        # Create task to cancel, yield to let create coroutine run
        app_context.timer_instance.create(10000, print, "unit_test")
        asyncio.run(self.sleep(10))

        # Cancel task, yield to let cancel coroutine run
        app_context.timer_instance.cancel("unit_test")
        asyncio.run(self.sleep(10))

        # Confirm task is NOT in queue
        rules = [time for time, rule in app_context.timer_instance.schedule.items()
                 if rule[0] == "unit_test"]
        self.assertEqual(len(rules), 0)

    def test_create_at_same_time(self):
        # Create 3 tasks at same time (different names so they aren't
        # considered duplicates and canceled)
        app_context.timer_instance.create(10000, print, "test1")
        app_context.timer_instance.create(10000, print, "test2")
        app_context.timer_instance.create(10000, print, "test3")
        # Yield to let create coroutine run
        asyncio.run(self.sleep(10))

        # Find expiration timestamps of each task
        for i in app_context.timer_instance.schedule:
            if app_context.timer_instance.schedule[i][0] == "test1":
                test1_expiration = i
            elif app_context.timer_instance.schedule[i][0] == "test2":
                test2_expiration = i
            elif app_context.timer_instance.schedule[i][0] == "test3":
                test3_expiration = i

        # Each timestamp should be 1 ms later than the one before
        self.assertEqual((test2_expiration - test1_expiration), 1)
        self.assertEqual((test3_expiration - test2_expiration), 1)

    def test_loop(self):
        # Get start epoch time
        start_time = time.time()

        # Create 2 timers expiring in 1 second and 5 seconds respectively
        app_context.timer_instance.create(1000, self.callback1, 'test1')
        app_context.timer_instance.create(5000, self.callback2, 'test2')

        # Run event loop for 1.1 seconds
        asyncio.run(self.sleep(1100))

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

        # Confirm loop not paused
        app_context.timer_instance.pause = False
        self.assertFalse(app_context.timer_instance.pause)

        # Create timer expiring in 2 seconds, run event loop for 500ms
        app_context.timer_instance.create(2000, self.callback1, 'test1')
        asyncio.run(self.sleep(500))

        # Confirm callback1 did NOT run
        self.assertFalse(self.callbacks['test1']['called'])

        # Confirm loop is paused (no timer due in next 1000ms)
        self.assertTrue(app_context.timer_instance.pause)

        # Run event loop for another 1.6 seconds, confirm callback1 was called
        asyncio.run(self.sleep(1600))
        self.assertTrue(self.callbacks['test1']['called'])

        # Confirm callback ran within 50ms of expected time
        elapsed_time = self.callbacks['test1']['time'] - start_time
        self.assertTrue(1.95 <= elapsed_time <= 2.05)

    @cpython_only
    def test_empty_loop(self):
        # Clear queue and schedule
        app_context.timer_instance.queue = []
        app_context.timer_instance.schedule = {}

        # Confirm loop not paused
        app_context.timer_instance.pause = False
        self.assertFalse(app_context.timer_instance.pause)

        # Run event loop for 100ms (branch coverage for iterating empty queue)
        asyncio.run(self.sleep(100))

        # Confirm loop paused, hardware timer deinitialized
        self.assertTrue(app_context.timer_instance.pause)
        self.assertIsNone(app_context.timer_instance.timer.start_time)

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
            app_context.timer_instance.create(10, self.callback1, 'test1')

        # Schedule the callback to run immediately
        app_context.timer_instance.create(0, callback_that_creates_timer, 'test')

        # Run event loop for 100ms to allow both timers to complete
        asyncio.run(self.sleep(100))

        # Confirm the timer created by callback ran
        self.assertTrue(self.callbacks['test1']['called'])
