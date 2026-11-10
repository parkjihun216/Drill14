import unittest
from unittest.mock import Mock, patch

import bird
import game_framework


class BirdSizeTests(unittest.TestCase):
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

    def make_bird(self, scale):
        with patch.object(bird.random, 'uniform', side_effect=[scale, 300.0]):
            return bird.Bird()

    def test_minimum_middle_and_maximum_sizes_keep_image_ratio(self):
        for scale, expected_width in ((1.0, 30.0), (1.25, 37.5), (1.5, 45.0)):
            with self.subTest(scale=scale):
                subject = self.make_bird(scale)
                self.assertAlmostEqual(subject.width, expected_width)
                self.assertAlmostEqual(subject.height / subject.width, (506 / 3) / (918 / 5))
                # 단위 환산의 부동소수점 오차(예: 45.00000000000001)를 허용한다.
                self.assertGreaterEqual(subject.width, 30.0 - 1e-9)
                self.assertLessEqual(subject.width, 45.0 + 1e-9)

    def test_larger_birds_keep_size_and_stay_inside_during_flight(self):
        for scale in (1.0, 1.25, 1.5):
            with self.subTest(scale=scale):
                subject = self.make_bird(scale)
                original_size = subject.width, subject.height
                for dt in (0.01, 0.1, 1.0, 10.0, 100.0):
                    game_framework.frame_time = dt
                    subject.update()
                    self.assertEqual((subject.width, subject.height), original_size)
                    self.assertGreaterEqual(subject.x - subject.width / 2, 0)
                    self.assertLessEqual(subject.x + subject.width / 2, 1600)
                    self.assertGreaterEqual(subject.y - subject.height / 2, 0)
                    self.assertLessEqual(subject.y + subject.height / 2, 600)


if __name__ == '__main__':
    unittest.main()
