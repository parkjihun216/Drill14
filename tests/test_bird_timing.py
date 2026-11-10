import unittest
from unittest.mock import Mock, patch

import bird
import game_framework


class BirdTimingTests(unittest.TestCase):
    def setUp(self):
        for target, name, value in (
            (bird.Bird, 'image', Mock(w=918, h=506)),
            (bird, 'get_canvas_width', lambda: 1600),
            (bird, 'get_canvas_height', lambda: 600),
        ):
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.addCleanup(setattr, game_framework, 'frame_time', 0.0)
        with patch.object(bird.random, 'uniform', side_effect=[1.0, 300.0]):
            self.subject = bird.Bird()

    def test_full_wingbeat_returns_to_same_pose(self):
        for initial_frame in (0.25, 4.75, 9.5, 13.75):
            with self.subTest(initial_frame=initial_frame):
                self.subject.frame = initial_frame
                game_framework.frame_time = 0.5
                self.subject.update()
                self.assertAlmostEqual(self.subject.frame, initial_frame)
                self.assertLess(int(self.subject.frame), 14)

    def test_left_edge_reflects_remaining_distance(self):
        left = self.subject.width / 2
        self.subject.x = left + 5.0
        self.subject.direction = -1
        game_framework.frame_time = 0.1
        self.subject.update()
        expected_distance = (30 * 1000 / 3600) * (10 / 0.3) * 0.1
        self.assertAlmostEqual(self.subject.x, left + expected_distance - 5.0)
        self.assertEqual(self.subject.direction, 1)

    def test_multiple_round_trips_preserve_position_and_direction(self):
        self.subject.x = 300.0
        self.subject.direction = -1
        # 양 끝 사이를 3회 왕복하면 출발 위치와 방향으로 돌아와야 한다.
        path_length = 2 * (1600 - self.subject.width)
        game_framework.frame_time = 3 * path_length / bird.FLIGHT_SPEED_PPS
        self.subject.update()
        self.assertAlmostEqual(self.subject.x, 300.0)
        self.assertEqual(self.subject.direction, -1)


if __name__ == '__main__':
    unittest.main()
