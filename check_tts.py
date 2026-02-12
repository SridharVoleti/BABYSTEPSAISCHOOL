#!/usr/bin/env python
try:
    from TTS.api import TTS
    print('TTS import successful')
except ImportError as e:
    print(f'TTS import failed: {e}')
