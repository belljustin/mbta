import os
from abc import abstractmethod
from contextlib import AbstractContextManager
from typing import ClassVar, Self

from PIL import Image, ImageDraw, ImageFont

from mbta.mbta import Board

class Display(AbstractContextManager):
    @abstractmethod
    def write(self, board: Board):
        pass

class StdoutDisplay(Display):
    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def write(self, board: Board):
        print(f"{board.route_name}, {board.stop_name}")
        print(*[(x.headsign, x.countdown) for x in board.arrivals][:3])

assetsdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')

font20 = ImageFont.truetype(os.path.join(assetsdir, 'Font.ttc'), 20)
font15 = ImageFont.truetype(os.path.join(assetsdir, 'Font.ttc'), 15)

class PILDisplay(Display):
    width: ClassVar[int] = 250
    height: ClassVar[int] = 122
    padding: ClassVar[int] = 5

    image: Image

    def __enter__(self) -> Self:
        self.image = Image.new('1', (PILDisplay.width, PILDisplay.height), 255)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.image.close()
    
    def _prepare_image(self, board):
        self.image = Image.new('1', (PILDisplay.width, PILDisplay.height), 255)

        draw = ImageDraw.Draw(self.image)
        draw.text((PILDisplay.padding, PILDisplay.padding), board.route_name, font=font20, fill=0)
        draw.text((PILDisplay.padding, PILDisplay.padding+20), board.stop_name, font=font15, fill=0)

        if len(board.arrivals) > 0:
            arrival = board.arrivals[0]
            arrTime1 = arrival.countdown
            arrTime1Mask = font20.getmask(arrTime1)
            draw.text((PILDisplay.padding, PILDisplay.height-2*arrTime1Mask.size[1]-4*PILDisplay.padding), arrival.headsign, font=font20)
            draw.text((PILDisplay.width - arrTime1Mask.size[0]-PILDisplay.padding, PILDisplay.height-2*arrTime1Mask.size[1]-4*PILDisplay.padding), arrTime1, font=font20)
        
        if len(board.arrivals) > 1:
            arrival = board.arrivals[1]
            arrTime2 = arrival.countdown
            arrTime2Mask = font20.getmask(arrTime2)
            draw.text((PILDisplay.padding, PILDisplay.height-arrTime2Mask.size[1]-2*PILDisplay.padding), arrival.headsign, font=font20)
            draw.text((PILDisplay.width - arrTime2Mask.size[0]-PILDisplay.padding, PILDisplay.height-arrTime2Mask.size[1]-2*PILDisplay.padding), arrTime2, font=font20)


    def write(self, board: Board):
        self._prepare_image(board)
        self.image.show()