import librosa
import librosa.display
import matplotlib.pyplot as plt
import util
import essentia
import essentia.standard as ess
from music21 import *
from librosa.core import hz_to_note, time_to_frames, frames_to_time
from onset import get_onset_frames
from pitch import detect_pitch
from chords import get_chords
from duration import get_durations
from scipy.signal import butter, sosfilt

def transcribe(filename):
  sr = 44100
  environment.set('musicxmlPath', '/usr/bin/musescore')

  y, sr = librosa.load(filename, sr=sr)

  tempo = get_tempo(y)
  print tempo

  # Get onset times.
  onset_frames = get_onset_frames(filename, sr)

  # print frames_to_time(onset_frames, sr)

  # print onset_frames

  durations = get_durations(onset_frames)

  # print durations

  # Filter the signal.
  filtered_y = bandpass_filter(y, sr, 80., 4000.)

  # chords = get_chords(filename, filtered_y, sr)
  # print chords

  # Detect pitch with different methods:
  # pitches = detect_pitch(filtered_y, sr, onset_frames, 'min_stft')
  # pitches = detect_pitch(filtered_y, sr, onset_frames, 'autocorr')
  pitches = detect_pitch(filtered_y, sr, onset_frames, 'yin')
  # pitches = detect_pitch(filtered_y, sr, onset_frames, 'klapuri')

  notes = pitches_to_notes(pitches)

  # Convert to Music21 stream and export to MusicXML file.
  score = get_score(notes, durations)

  score.write("musicxml", "static/piece.mxl")

  # plot.plot_waveform(y)
  # util.plot_spectrogram(librosa.stft(y), sr)
  # plt.close('all')
  
  return notes

def pitches_to_notes(pitches):
  notes = []
  for pitch in pitches:
    notes.append(hz_to_note(pitch))
  return notes

def get_score(notes, durations):
  score = stream.Score()
  score.insert(0, clef.TrebleClef())
  # Time Signature
  # Key Signature
  score.insert(instrument.AcousticGuitar())
  print score.getInstrument().instrumentName
  score.insert(0, tempo.MetronomeMark(number=120))
  notes = sum(notes, [])
  for i in range(0, len(notes)):
    print notes[i]
    f = note.Note(notes[i])
    f.duration = duration.Duration(durations[i])
    score.append(f)

  return score

def bandpass_filter(y, sr, lowcut, highcut):
  # Setup parameters.
  nyquist_rate = sr / 2.
  filter_order = 3
  normalized_low = lowcut / nyquist_rate
  normalized_high = highcut / nyquist_rate

  sos = butter(filter_order, [normalized_low, normalized_high],
    btype='bandpass', output='sos')
  
  y = sosfilt(sos, y)
  return y

def get_tempo(y):
  tempo_estimator = ess.PercivalBpmEstimator()
  bpm = tempo_estimator(y)
  return util.round_to_base(bpm, 5)