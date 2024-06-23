# Clip Merge X

Cut MTS Files from camcorder and merge them to one video file.

Features:
- Configuration based cutting via a csv file. Use `--csv_file`. If not given all files from `--input_dir` is taken.
- Add automatic fading and date (which is taken from mtime of file). Use `--effects`
- Output containers may be used: mp4, webm, mkv
- Speficy Codec: h264 (standard for mp4), h265, vp9 (standard for webm), av1 (standard for mkv)
- automatic resizing to 720p (for all but av1)

Note: 
The script has been adopted to personal requirments. This may differ to yours.

## Requirements

Tested on Debian Bookworm with the following extra packages:
- Python3
- ffmpeg 

## Example usage

A folder with MTS files given:

```sh
tree input
input
├── 00005.MTS
├── 00006.MTS
├── 00011.MTS
└── 00012.MTS

1 directory, 4 files
```

A CSF-File given:

```sh
cat test_mini.csv 
file;00005.MTS;00:00:45-00:01:05;00:01:30
file;00011.MTS;00:00:10-00:00:20;
file;00012.MTS
```

Each line has to have the folling format:

```sh
file;<name in folder>;(<start>(-<end>;)*
```

Example calls:

```sh
./clip-merge-x.sh -i input --csv_list test_mini.csv --effects --codec av1 --output_file test-av1.mkv
```

