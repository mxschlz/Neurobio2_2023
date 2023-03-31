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
    setup = Str("FREEFIELD", group="status", dsec="Name of the experiment setup")

    def _get_total_trial(self):
        return self.trial_number * self.conditions


class VocodingExperiment(ExperimentLogic):

    setting = VocodingSetting()
    data = ExperimentData()  # dont worry about this
    device = RX8RP2Device()
    sequence = slab.Trialsequence(conditions=setting.conditions, n_reps=setting.trial_number)

    def setup_experiment(self, info=None):
        self.load_stimuli()

    def prepare_trial(self):
        this_trial = self.sequence.__next__()

    def start_trial(self):
        pass

    def stop_trial(self):
        pass

    def load_stimuli(self):
        pass

if __name__ == "__main__":
    exp = VocodingExperiment()
    exp.start()