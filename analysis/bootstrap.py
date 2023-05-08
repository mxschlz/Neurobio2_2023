import numpy as np
import mne
import matplotlib.pyplot as plt
import os

# Load your original epochs data
filename = "03d3rc-epo.fif"
datapath = "D:\\EEG\\example\\data\\03d3rc"
epochs_orig = mne.read_epochs(os.path.join(datapath, filename))

# Define the number of bootstrap iterations --> number of simulated subjects
n_bootstraps = 5

# Get the unique condition names in the original epochs data
unique_conditions = epochs_orig.event_id.keys()

# Create an empty list to store the resampled epochs data for each condition
epochs_sampled = {cond: [] for cond in unique_conditions}

# Loop through each bootstrap iteration
for i in range(n_bootstraps):

    # Split the resampled bootstrap sample into epochs for each condition
    for cond in unique_conditions:
        # Define the size of the bootstrap samples (can be the same size as the original data)
        sample_size = len(epochs_orig[cond])

        # Create a bootstrap sample by randomly selecting epochs from each condition in the original data
        sample_indices = np.random.choice(sample_size, size=sample_size, replace=True)  # with replacement --> bootstrap
        epochs_cond = epochs_orig[cond][sample_indices]
        epochs_sampled[cond].append(epochs_cond)

sub01 = [epochs_sampled[cond][0].average() for cond in unique_conditions]
sub02 = [epochs_sampled[cond][1].average() for cond in unique_conditions]

# plot condition A against condition B
mne.viz.plot_compare_evokeds([[sub01[0], sub02[0], epochs_orig["A"].average()],
                              [sub01[1], sub02[1], epochs_orig["B"].average()]])

