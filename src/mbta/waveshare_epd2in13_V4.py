import os
import sys
import logging
from typing import Self

from mbta.display import PILDisplay
from mbta.mbta import Board

datadir = os.path.join(os.path.dirname(__file__), 'data')
libdir = os.path.join(os.path.dirname(__file__), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd2in13_V4

class WaveshareEpd2in13Display(PILDisplay):
    epd: epd2in13_V4.EPD

    def __enter__(self) -> Self:
        super().__enter__()
        self.epd = epd2in13_V4.EPD()
        self.epd.init()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__enter__()

        logging.info("Clear...")
        self.epd.init()
        self.epd.Clear(0xFF)
        
        logging.info("Goto Sleep...")
        self.epd.sleep()

        epd2in13_V4.epdconfig.module_exit(cleanup=True)

    def write(self, board: Board):
        self._prepare_image(board)

        try:
            logging.info("E-paper refresh")
            self.epd.Clear(0xFF)

            logging.info("1.Drawing on the image...")
            self.epd.display(self.epd.getbuffer(self.image))
                
        except IOError as e:
            logging.info(e)
