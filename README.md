# WACCA ACB Editor

## Credits
* Javaguru for the base code parsing acb, documentation, and more

## Usage

First, put a build of VGAudioCli in `external/vgaudio` and ffmpeg inside `external`.

TUI usage: `python wacca_song_editor.py tui`

### Append One Song

`python wacca_song_editor.py append-song --acb-path=MER_BGM.acb --awb=MER_BGM_V3_03 --song-path="/Users/raymonf/Downloads/song.flac"`

### Append List of Songs

`python wacca_song_editor.py append-song-list --acb-path=MER_BGM.acb --awb=MER_BGM_V3_03 --list-path="songlist.txt" `

Input (songlist.txt):
```
song1.ogg
song2.wav
song3.ogg
```

Output (inside MER_BGM_V3_03):
```
...
MER_BGM_S04_000
MER_BGM_S04_001
MER_BGM_S04_002
```

#### Notes

* There is a bug in the awb writer where the first song does not play properly. A workaround (until the bug is fixed) is to copy the first song to another index and then update the reference in the game as needed.
