from typing import Any, Dict, List
from owonHDS import owonHDS
import sys
import time
import re
import numpy as np
import pyqtgraph as pg

from pyqtgraph.Qt import QtCore

CHANNEL_COLORS = {"CH1": "y", "CH2": "b"}


def float_from_str(val: str) -> float:
    _prefix = {
        "p": 1e-12,  # pico
        "n": 1e-9,  # nano
        "u": 1e-6,  # micro
        "m": 1e-3,  # milli
        "c": 1e-2,  # centi
        "d": 1e-1,  # deci
        "": 1,  # None
        "k": 1e3,  # kilo
        "M": 1e6,  # mega
        "G": 1e9,  # giga
        "T": 1e12,  # tera
    }

    m = re.match(r"^(?P<number>[-\d.]+)(?P<prefix>\w?)(?P<units>\w)$", val)
    if not m:
        raise FloatingPointError()

    return float(m.group("number")) * _prefix[m.group("prefix")]


def main() -> int:
    global CHANNEL_COLORS

    scope = owonHDS()
    scope.find_device()

    if not scope.dev:
        print("No device found")
        return -1
    else:
        id = scope.device_id()
        if id:
            print(f"Device {id.manufacturer} {id.model} found at port {scope.dev.port_number}:{scope.dev.address}\n\n")
        else:
            print("Device found, but could not identify.")
            return -2

    app = pg.mkQApp()

    win = pg.GraphicsLayoutWidget(show=True)
    win.resize(640, 480)
    win.setWindowTitle("HDS200 Streamer")

    pg.setConfigOptions(antialias=True)

    graph: pg.PlotItem = win.addPlot()
    graph.setClipToView(True)

    def update():
        nonlocal graph, scope

        start = time.time()

        graph.clearPlots()
        info = scope.get_screen_info()
        for channel in info.CHANNEL:
            channel_name = channel.NAME
            channel_enabled = channel.DISPLAY == "ON"
            if not channel_enabled:
                continue

            waveform = graph.plot(title=channel, pen=CHANNEL_COLORS[channel_name])

            samples = np.frombuffer(scope.get_data(channel_name), dtype=np.int8)
            # waveform.setData(samples)
            volts_per_div = float_from_str(channel.SCALE)
            sample_offset = int(channel.OFFSET)
            num_divs = 5
            unit_data = (samples - sample_offset) / 128
            voltage = unit_data * volts_per_div * num_divs
            timestep = float_from_str(info.TIMEBASE.SCALE)
            time_offset = int(info.TIMEBASE.HOFFSET)
            num_samples = len(samples)
            time_start = -1 * (num_samples / 2) * timestep
            time_stop = (num_samples / 2) * timestep
            timesteps = np.arange(time_start, time_stop, timestep)
            waveform.setData(y=voltage, x=timesteps)

        end = time.time()
        print(f"Update took {end-start:.2f}s")

    update()

    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(1000)

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
