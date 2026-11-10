import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import bird
import game_framework
import game_world
import play_mode


class BirdTests(unittest.TestCase):
    def setUp(self):
        self.image = Mock(w=918, h=506)
        bird.Bird.image = None
        self.addCleanup(setattr, bird.Bird, 'image', None)
        self.addCleanup(setattr, game_framework, 'frame_time', 0.0)
        self.addCleanup(game_world.clear)
        for name, value in [('load_image', self.image),
                            ('get_canvas_width', 1600),
                            ('get_canvas_height', 600)]:
            patcher = patch.object(bird, name, return_value=value)
            mock = patcher.start()
            self.addCleanup(patcher.stop)
            if name == 'load_image':
                self.loader = mock

    def simulate(self, steps):
        # FPS 비교에서는 같은 크기와 초기 상태의 새를 사용한다.
        with patch.object(bird.random, 'uniform', side_effect=[1.0, 300.0]):
            subject = bird.Bird()
        subject.x, subject.direction, subject.frame = 300.0, 1, 2.25
        for dt in steps:
            game_framework.frame_time = dt
            subject.update()
        return subject

    def test_speed_and_wingbeat_use_seconds(self):
        result = self.simulate([0.25])
        self.assertAlmostEqual(result.x, 300 + (30 * 1000 / 3600) * (10 / 0.3) * 0.25)
        self.assertAlmostEqual(result.frame, 9.25)
        self.assertAlmostEqual(result.width, 30.0)
        self.assertAlmostEqual(result.height, 27.5599128540305)

    def test_same_elapsed_time_at_different_frame_rates(self):
        duration = 17.237  # 여러 번 반사한 뒤에도 위치와 위상이 같은지 확인
        expected = self.simulate([duration])
        schedules = [[1 / fps] * int(duration * fps)
                     + [duration - int(duration * fps) / fps]
                     for fps in (30, 60, 144)]
        schedules.append([0.007, 0.130, 0.3, 1.2, 5.0, 10.6])
        for steps in schedules:
            with self.subTest(steps=len(steps)):
                result = self.simulate(steps)
                self.assertAlmostEqual(result.x, expected.x, places=8)
                self.assertAlmostEqual(result.frame, expected.frame, places=8)
                self.assertEqual(result.direction, expected.direction)

    def test_reflection_preserves_overshoot_and_image_stays_inside(self):
        subject = bird.Bird()
        right = 1600 - subject.width / 2
        subject.x, subject.direction = right - 5, 1
        game_framework.frame_time = 0.1
        subject.update()
        self.assertAlmostEqual(subject.x, right - (bird.FLIGHT_SPEED_PPS * 0.1 - 5))
        self.assertEqual(subject.direction, -1)
        for dt in (0.0, 1.0, 100.0, 0.003):
            game_framework.frame_time = dt
            subject.update()
            self.assertGreaterEqual(subject.x, subject.width / 2)
            self.assertLessEqual(subject.x, right)

    def test_all_fourteen_cells_and_direction(self):
        subject = bird.Bird()
        cells = []
        for frame in range(14):
            subject.frame = frame + 0.25
            subject.direction = 1
            subject.draw()
            args = self.image.clip_composite_draw.call_args.args
            left, bottom, width, height = args[:4]
            self.assertGreaterEqual(left, 0)
            self.assertGreaterEqual(bottom, 0)
            self.assertLessEqual(left + width, 918)
            self.assertLessEqual(bottom + height, 506)
            self.assertEqual(args[5], '')
            self.assertEqual(args[-2:], (subject.width, subject.height))
            cells.append(args[:4])
        self.assertEqual(len(set(cells)), 14)
        self.assertEqual(cells[0], (0, 338, 183, 168))
        self.assertEqual(cells[5], (0, 169, 183, 169))
        self.assertEqual(cells[13], (550, 0, 184, 169))
        subject.direction = -1
        subject.draw()
        self.assertEqual(self.image.clip_composite_draw.call_args.args[5], 'h')

    def test_ten_birds_share_one_image_and_mode_cleans_up(self):
        with patch.object(play_mode, 'Boy'), patch.object(play_mode, 'Grass'):
            for _ in range(2):
                play_mode.init()
                birds = [obj for layer in game_world.world for obj in layer
                         if isinstance(obj, bird.Bird)]
                self.assertEqual(len(birds), 10)
                self.assertEqual(len({obj.x for obj in birds}), 10)
                self.assertTrue(all(obj.image is self.image for obj in birds))
                play_mode.finish()
                self.assertTrue(all(not layer for layer in game_world.world))
        self.loader.assert_called_once_with('bird_animation.png')


class FrameworkTimeTests(unittest.TestCase):
    def test_current_elapsed_time_is_available_before_update(self):
        observed = []
        def handle_events():
            if len(observed) == 2:
                game_framework.quit()

        mode = SimpleNamespace(
            init=Mock(), render=Mock(),
            update=lambda: observed.append(game_framework.frame_time),
            handle_events=handle_events,
        )
        with patch.object(game_framework.time, 'sleep'), patch.object(
                game_framework.time, 'perf_counter', side_effect=[10, 10.02, 10.12, 10.15]):
            game_framework.run(mode)
        self.assertEqual(len(observed), 2)
        self.assertAlmostEqual(observed[0], 0.02)
        self.assertAlmostEqual(observed[1], 0.1)
        self.assertEqual(mode.render.call_count, 2)
        game_framework.stack = []
        game_framework.frame_time = 0.0


if __name__ == '__main__':
    unittest.main()
