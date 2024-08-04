import logging
import itertools
import argparse
import time

from mbta.mbta import get_board
from mbta.display import Display, StdoutDisplay, PILDisplay

logger = logging.getLogger(__name__)

display_types = {
    "stdout": StdoutDisplay,
    "pillow": PILDisplay,
}

try:
    from mbta.waveshare_epd2in13_V4 import WaveshareEpd2in13Display
    display_types["pi"] = WaveshareEpd2in13Display
except OSError:
    logger.warn("Could not load waveshare_epd2in13_v4")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--display", help="Display type. One of ['stdout', 'pillow', 'pi']", type=str)

    args = parser.parse_args()

    display_arg = args.display if args.display is not None else "stdout"

    display_type = display_types[display_arg]
    values = [
        ('Green-E', 'place-mgngl'),
        ('Red', 'place-cntsq'),
        ('83', '2454'),
    ]
    with display_type() as display:
        for x in itertools.cycle(values):
            try:
                board = get_board(x[0], x[1])
                display.write(board)
                time.sleep(1)
            except Exception as e:
                logger.warn(e)


if __name__ == '__main__':
    main()
