from labplatform.core.Setting import ExperimentSetting
from labplatform.core.ExperimentLogic import ExperimentLogic
from labplatform.core.Data import ExperimentData
from labplatform.core.Subject import Subject, SubjectList
from labplatform.config import get_config
import os
from traits.api import List, Str, Int, Dict, Float, Any
import slab
import time
import numpy as np
import logging
import datetime
import pathlib
import random
from experiment.RXRP2Device import RX8RP2Device
from experiment.config import vocoding_config

log = logging.getLogger(__name__)
cfg = vocoding_config


class VocodingSetting(ExperimentSetting):

    experiment_name = Str('Vocoding', group='status', dsec='name of the experiment', noshow=True)
    conditions = Int(cfg.conditions, group="primary", dsec="Number of different vocoding bandwidths")
    trial_number = Int(cfg.trial_number, group='status', dsec='Number of trials in each condition')
    stim_duration = Float(cfg.stim_duration, group='status', dsec='Duration of each stimulus, (s)')
    deviant_freq = Float(cfg.deviant_freq, group='status', dsec='Deviant frequency')
    setup = Str("FREEFIELD", group="status", dsec="Name of the experiment setup")

    def _get_total_trial(self):
        return self.trial_number * self.conditions


class VocodingExperiment(ExperimentLogic):

    setting = VocodingSetting()
    data = ExperimentData()  # dont worry about this
    results = slab.ResultsFile(subject="Hannah", folder=os.path.join(get_config("DATA_ROOT")))
    device = RX8RP2Device()
    sequence = slab.Trialsequence(conditions=setting.conditions,
                                  n_reps=setting.trial_number,
                                  deviant_freq=setting.deviant_freq)
    stim_path = os.path.join(get_config("SOUND_ROOT"), "neurobio2_2023", "normalized_2")
    stim_dict = dict()
    sound_to_play = Any()
    deviant_sound = slab.Sound.chirp(0.3)  # same length as other stimuli
    response = Int()
    time_0 = Float()
    rt = Any()

    def setup_experiment(self, info=None):
        self.load_stimuli()

    def prepare_trial(self):
        this_condition = self.sequence.__next__()
        if not this_condition == 0:
            self.sound_to_play = random.choice(self.stim_dict[this_condition])
        elif this_condition == 0:
            self.sound_to_play = self.deviant_sound
        self.results.write(self.sequence.this_n, "trial_n")
        self.results.write(this_condition, "condition_this_trial")

    def start_trial(self):
        self.time_0 = time.time()  # starting time of the trial
        self.sound_to_play.play()
        if self.sequence.this_trial == 0:
            self.device.wait_for_button()
            self.response = self.device.get_response()
            self.results.write(data=self.response, tag="response")
            self.rt = int(round(time.time() - self.time_0, 3) * 1000)
            self.results.write(data=self.rt, tag="reaction_time")

    def stop_trial(self):
        self.device.pause()

    def load_stimuli(self):
        for directory in os.listdir(self.stim_path):
            sound_list = list()
            for sound_file in os.listdir(os.path.join(self.stim_path, directory)):
                sound = slab.Sound.read(os.path.join(self.stim_path, directory, sound_file))
                sound_list.append(sound)
            self.stim_dict[directory] = sound_list
        ori_sound_list = list()
        for ori_sound_file in os.listdir(os.path.join(get_config("SOUND_ROOT"), "neurobio2_2023\\original\\N_LUFS")):
            ori_sound = slab.Sound.read(os.path.join(get_config("SOUND_ROOT"), "neurobio2_2023\\original\\N_LUFS", ori_sound_file))
            ori_sound_list.append(ori_sound)
        self.stim_dict["original"] = ori_sound_list


if __name__ == "__main__":
    exp = VocodingExperiment()
    exp.start()