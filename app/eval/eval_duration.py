import sys
import os

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if not path in sys.path:
  sys.path.insert(1, path)
del path

import app
import duration
import librosa

APP_ROOT = app.APP_ROOT
AUDIO_FOLDER = os.path.join(APP_ROOT, 'static/audio/')

def eval():
  scores = []

  # TODO: Evaluate durations.
  scores.append(get_score('softkitty.mp3', 22))
  scores.append(get_score('unknown.mp3', 53))
  scores.append(get_score('unknown2.mp3', 39))

  print "Average error:"
  print sum(scores) / float(len(scores))

def get_score(filename, correct):