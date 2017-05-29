import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import plot
import music21
from music21 import *
from librosa.core import hz_to_note, frames_to_time
from onset import get_onset_frames
from scipy.signal import butter, lfilter
from frequency_estimator import freq_from_autocorr, freq_from_hps

def transcribe(filename):
  sr = 44100
  music21.environment.set('musicxmlPath', '/usr/bin/musescore')

  y, sr = librosa.load(filename, sr=sr)

  # Get onset times.
  onset_frames = get_onset_frames(filename, sr)

  # Filter the signal.
  # filtered_y = bandpass_filter(y, sr, 80., 4000.)
  filtered_y = y

  # D = librosa.stft(filtered_y)

  # Detect pitch with different methods:
  stft_pitches = detect_pitch(filtered_y, sr, onset_frames, 'stft')
  print stft_pitches

  autocorr_pitches = detect_pitch(filtered_y, sr, onset_frames, 'autocorr')
  print autocorr_pitches

  hps_pitches = detect_pitch(filtered_y, sr, onset_frames, 'hps')
  print hps_pitches

  pitches = hps_pitches

  notes = []
  for pitch in pitches:
    notes.append(hz_to_note(pitch))

  # Convert to Music21 stream and export to MusicXML file.
  note_stream = convert_to_notes(notes)

  note_stream.write("musicxml", "static/piece.mxl")

  # plot.plot_waveform(y)
  # plot.plot_spectrogram(D, sr)
  # plt.close('all')
  
  return notes

def convert_to_notes(pitches):
  notes = stream.Stream()
  pitches = sum(pitches, [])
  for pitch in pitches:
    f = note.Note(pitch)
    notes.append(f)

  return notes

# Checking the pitch some frames the onset time increased precision.
def detect_pitch(y, sr, onset_frames, method='stft', onset_offset=0, fmin=80, fmax=4000):
  result_pitches = []

  pitches, magnitudes = librosa.piptrack(y=y, 
    sr=sr, fmin=fmin, fmax=fmax)

  if method == 'stft':
      for i in range(0, len(onset_frames)):
        onset = onset_frames[i] + onset_offset
        index = magnitudes[:, onset].argmax()
        pitch = pitches[index, onset]
        # duration = detect_duration(magnitudes, index, onset)
        if (pitch != 0):
          result_pitches.append(pitch)

  elif method == 'autocorr':
    slices = segment_signal(y, sr, onset_frames)
    for segment in slices:
      pitch = freq_from_autocorr(segment, sr)
      result_pitches.append(pitch)

  elif method == 'hps':
    slices = segment_signal(y, sr, onset_frames)
    for segment in slices:
      pitch = freq_from_hps(segment, sr)
      result_pitches.append(pitch)
  return result_pitches

# For each note played, get the n strongest peaks in the frequency spectrum.
def get_peaks(pitches, magnitudes, onset_frames, n=5):
    candidate_list = []

    for i in range(0, len(onset_frames)):
      candidates = []
      onset = onset_frames[i] + 1
      indices = np.argpartition(magnitudes[:, onset], 0-n)[0-n:]

      for j in indices:
        candidates.append(pitches[j, onset])

      candidate_list.append(candidates)

    return candidate_list

def bandpass_filter(y, sr, lowcut, highcut):
  # Setup parameters.
  nyquist_rate = sr / 2.
  filter_order = 1001
  normalized_low = lowcut / nyquist_rate
  normalized_high = highcut / nyquist_rate

  b, a = butter(filter_order, [normalized_low, normalized_high], btype='bandpass')
  
  y = lfilter(b, a, y)
  return y

def segment_signal(y, sr, onset_frames):

  # This splits the signal into slices that sum up to the whole signal according
  # to onset_bt.
  #oenv = librosa.onset.onset_strength(y=y, sr=sr)
  #onset_bt = librosa.onset.onset_backtrack(onset_frames, oenv)

  #new_onset_bt = librosa.frames_to_samples(onset_bt)

  #slices = np.split(y, new_onset_bt[1:])
  
  # TODO: Choose appropriate offsets.
  offset_start = int(librosa.time_to_samples(0.01, sr))
  offset_end = int(librosa.time_to_samples(0.1, sr))

  slices = np.array([y[i : i + offset_end] for i
    in librosa.frames_to_samples(onset_frames)])

  return slices

def remove_values_from_list(l, val):
  return [value for value in l if value != val]

def detect_duration(magnitudes, bin, time_frame):
  # TODO: This is going to get messy if there is a new note played before
  # the last note has finished.
  duration = 0
  while magnitudes[bin, time_frame] > 1:
    duration += 1
    time_frame += 1

  return duration