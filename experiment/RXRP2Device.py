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

class RX8RP2DeviceSetting(DeviceSetting):
    device_freq = Float(48828, group='status', dsec='sampling frequency of the device (Hz)')
    rcx_file_RP2 = Str('button_rec.rcx', group='status', dsec='the rcx file for RP2')
    rcx_file_RX8 = Str('eeg_triggers.rcx', group='status', dsec='the rcx file for RX8')
    processor_RP2 = Str('RP2', group='status', dsec='name of the processor')
    processor_RX8 = Str('RX8', group='status', dsec='name of the processor')
    connection = Str('GB', group='status', dsec='Type of the processor connection')
    rx8index = Int(2, group='primary', dsec='index of the device to connect to')
    max_stim_length_n = Int(500000, group='status', dsec='maximum length for stimulus in number of data points')
    device_type = 'RX8RP2Device'

class RX8RP2Device(Device):
    """
    the buffer 'PulseTTL' will not reset when calling pause/start. to reset the buffer, need to
    send software trigger 2 to the circuit, or use method reset_buffer
    """
    setting = RX8RP2DeviceSetting()
    buffer = Any()
    RP2 = Any()
    RX8 = Any()
    _use_default_thread = True


    def _initialize(self, **kwargs):
        expdir = os.path.join(get_config('DEVICE_ROOT'), "neurobio2_2023")
        self.RP2 = tdt.initialize_processor(processor=self.setting.processor_RP2,
                                            connection=self.setting.connection,
                                            index=1,
                                            path=os.path.join(expdir, self.setting.rcx_file_RP2))
        self.RX8 = tdt.initialize_processor(processor=self.setting.processor_RX8,
                                            connection=self.setting.connection,
                                            index=self.setting.rx8index,
                                            path=os.path.join(expdir, self.setting.rcx_file_RP2))

        # not necessarily accurate
        TDT_freq = self.RP2.GetSFreq()  # not necessarily returns correct value
        if abs(TDT_freq - self.setting.device_freq) > 1:
            log.warning('TDT sampling frequency is different from that specified in software: {} vs. {}'.
                        format(TDT_freq, self.setting.device_freq))
            # self.setting.device_freq = self.handle.GetSFreq()

    def _configure(self, **kwargs):
        pass

    def _pause(self):
        pass

    def _start(self):
        self.RX8.trigger("zBusA", proc=self.RX8)

    def _stop(self):
        self.RP2.halt()
        self.RX8.halt()

    def wait_for_button(self):  # stops the circuit as long as no button is being pressed
        log.info("Waiting for button press ...")
        while not self.handle.GetTagVal("response"):
            time.sleep(0.1)  # sleeps while the response tag in the rcx circuit does not yield 1

    def get_response(self):  # collects response, preferably called right after wait_for_button
        log.info("Acquiring button response ... ")
        # because the response is stored in bit value, we need the base 2 log
        try:
            response = int(np.log2(self.RP2.GetTagVal("response")))
        except OverflowError:
            response = self.RP2.GetTagVal("response")
        return response

    def thread_func(self):
        if self.experiment:
            if self.experiment().sequence.this_trial != 0:
                if int(round(time.time() - self.experiment().time_0, 3) * 1000) > 1000:
                    self.experiment().process_event({'trial_stop': 0})
            elif self.experiment().sequence.this_trial != 0:
                if self.RP2.GetTagVal("response") > 0:
                    self.experiment().process_event({'trial_stop': 0})


if __name__ == "__main__":
    device = RX8RP2Device()