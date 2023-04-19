from labplatform.config import get_config
from labplatform.core.Device import Device
from labplatform.core.Setting import DeviceSetting
from traits.api import Float, Str, Any, Int
from labplatform.core import TDTblackbox as tdt
import logging
import os
import numpy as np
import time

log = logging.getLogger(__name__)


# TODO: try loading circuit only on the RX82


class RX8RP2DeviceSetting(DeviceSetting):
    device_freq = Float(48828, group='status', dsec='sampling frequency of the device (Hz)')
    rcx_file_RP2 = Str('play_buf.rcx', group='status', dsec='the rcx file for RP2')
    rcx_file_RX8 = Str('eeg_triggers.rcx', group='status', dsec='the rcx file for RX8')
    processor_RP2 = Str('RP2', group='status', dsec='name of the processor')
    processor_RX8 = Str('RX8', group='status', dsec='name of the processor')
    connection = Str('GB', group='status', dsec='Type of the processor connection')
    rx8index = Int([1, 2], group='primary', dsec='index of the device to connect to')
    max_stim_length_n = Int(500000, group='status', dsec='maximum length for stimulus in number of data points')
    device_type = 'RX8RP2Device'


class RX8RP2Device(Device):

    setting = RX8RP2DeviceSetting()
    buffer = Any()
    handle = Any()
    _use_default_thread = True

    def _initialize(self, **kwargs):
        expdir = os.path.join(get_config('DEVICE_ROOT'), "neurobio2_2023")
        self.handle = tdt.Processors()
        self.handle.initialize(proc_list=[["RX81", "RX8", os.path.join(expdir, self.setting.rcx_file_RX8)],
                                          ["RX82", "RX8", os.path.join(expdir, self.setting.rcx_file_RX8)],
                                          ["RP2", "RP2", os.path.join(expdir, self.setting.rcx_file_RP2)]],
                               connection=self.setting.connection,
                               zbus=True)

    def _configure(self, **kwargs):
        pass

    def _pause(self):
        pass

    def _start(self):
        self.handle.trigger("zBusA", proc=self.handle)

    def _stop(self):
        self.handle.halt()

    def wait_for_button(self):  # stops the circuit as long as no button is being pressed
        log.info("Waiting for button press ...")
        while not self.handle.read("response", proc="RP2"):
            time.sleep(0.1)  # sleeps while the response tag in the rcx circuit does not yield 1

    def get_response(self):  # collects response, preferably called right after wait_for_button
        log.info("Acquiring button response ... ")
        # because the response is stored in bit value, we need the base 2 log
        try:
            response = int(np.log2(self.handle.read("response", proc="RP2")))
        except OverflowError:
            response = self.handle.read("response", proc="RP2")
        return response

    def wait_to_finish_playing(self, proc="all", tag="playback"):
        if proc == "all":
            proc = list(self.handle.procs.keys())
        elif isinstance(proc, str):
            proc = [proc]
        logging.info(f'Waiting for {tag} on {proc}.')
        while any(self.handle.read(tag, proc=p) for p in proc):
            time.sleep(0.01)
        log.info('Done waiting.')

    def thread_func(self):
        if self.experiment:
            if self.experiment().sequence.this_trial != 0:
                if int(round(time.time() - self.experiment().time_0, 3)) > self.experiment().setting.trial_watch:
                    self.experiment().process_event({'trial_stop': 0})
            elif self.experiment().sequence.this_trial == 0:
                if self.handle.read("response", proc="RP2") > 0:
                    self.experiment().process_event({'trial_stop': 0})


if __name__ == "__main__":
    log.setLevel(logging.DEBUG)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    log.addHandler(ch)

    device = RX8RP2Device()
