"""실제 pico2d 리소스를 창 없이 렌더링하고 확인용 PNG를 저장한다."""

import os
from pathlib import Path
import random
import sys


def main():
    project_root = Path(__file__).resolve().parents[1]
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    os.environ['SDL_RENDER_DRIVER'] = 'software'

    import pico2d
    import sdl2
    from sdl2.sdlimage import IMG_SavePNG
    import bird
    import game_framework
    import game_world
    import play_mode

    output_dir = Path('tmp/bird-checks')
    output_dir.mkdir(parents=True, exist_ok=True)

    def save_snapshot(renderer, filename):
        surface = sdl2.SDL_CreateRGBSurfaceWithFormat(0, 1600, 600, 32, sdl2.SDL_PIXELFORMAT_RGBA32)
        if not surface:
            raise RuntimeError(sdl2.SDL_GetError())
        try:
            result = sdl2.SDL_RenderReadPixels(
                renderer, None, surface.contents.format.contents.format,
                surface.contents.pixels, surface.contents.pitch,
            )
            if result != 0:
                raise RuntimeError(sdl2.SDL_GetError())
            if IMG_SavePNG(surface, str(filename).encode('utf-8')) != 0:
                raise RuntimeError(sdl2.SDL_GetError())
        finally:
            sdl2.SDL_FreeSurface(surface)

    random.seed(16)  # 확인용 캡처만 재현 가능하게 한다. 게임 실행은 무작위다.
    pico2d.open_canvas(1600, 600)
    try:
        renderer = pico2d.open_canvas.__globals__['renderer']
        if not renderer:
            raise RuntimeError(sdl2.SDL_GetError())
        play_mode.init()
        birds = [o for layer in game_world.world for o in layer if isinstance(o, bird.Bird)]
        if len(birds) != 10:
            raise AssertionError(f'Expected 10 birds, got {len(birds)}')
        for frame in range(600):
            game_framework.frame_time = 1 / 60
            play_mode.update()
            if frame in (0, 299, 599):
                pico2d.clear_canvas()
                game_world.render()
                save_snapshot(renderer, output_dir / f'birds-{frame:03d}.png')
                pico2d.update_canvas()
        for index in range(14):
            for subject in birds:
                subject.frame = index
            play_mode.render()
        print('PASS: 10 birds, 600 updates, all 14 sprite cells rendered')
        print('Bird widths (px):', ', '.join(f'{o.width:.2f}' for o in birds))
        print('Snapshots:', output_dir.resolve())
    finally:
        play_mode.finish()
        pico2d.close_canvas()


if __name__ == '__main__':
    main()
