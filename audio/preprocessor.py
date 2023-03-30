import logging
import math
import os.path
import re
import tempfile

from audio import external
from audio.error import AudioPreprocessorError
from audio.preprocess_result import PreprocessResult


class AudioPreprocessor:
    log: logging.Logger = None

    def __init__(self):
        self.log = logging.getLogger("preprocessor")

        external.ensure_dependencies()

    def __try_delete_file(self, file_path: str, name: str = 'file') -> bool:
        if os.path.exists(file_path):
            try:
                self.log.debug(f"Attempting to delete {name} '{file_path}'")
                os.unlink(file_path)
                return True
            except OSError as e:
                self.log.warning(f"Could not delete {name} {file_path} because '{e}'", e)
                return False

    def get_audio_info(self, song_path: str) -> (str, int):
        """
        Calls ffmpeg with no arguments to obtain the file type and sample rate of the first stream

        :param: song_path: Path to song
        :return: Audio file type, sample rate in Hz
        """
        output, err = external.run_ffmpeg([
            "-i",
            song_path
        ])
        if err is not None:
            raise AudioPreprocessorError(f"ffmpeg error:\n{err}")

        # [('flac', '41000'), ...]
        streams = re.findall(r"Stream #.*: Audio: (.*), (\d+) Hz", output)
        if len(streams) < 1:
            raise AudioPreprocessorError("Couldn't extract sample rate because no streams were found")
        if len(streams) > 1:
            self.log.warning(
                f"Multiple audio streams were found. Using first stream ({streams[0][0]}, {streams[0][1]} Hz)")
        return streams[0][0], int(streams[0][1])

    def resample_audio(self, original_path) -> str:
        """
        :param: original_path: Path to original file
        :return: Path to the new, resampled wav file
        """
        temp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp.close() # dllm windows
        new_path = temp.name
        self.log.debug(f"Attempting to resample '{original_path}' to '{new_path}'")
        output, err = external.run_ffmpeg([
            "-y",  # automatically overwrite
            "-i", original_path,
            "-ar", "48000",
            new_path
        ])
        if err is not None:
            self.log.error(f"ffmpeg error: {err}")
            self.__try_delete_file(new_path)
            raise AudioPreprocessorError(f"ffmpeg error:\n{err}")

        self.log.debug(f"Successfully resampled to desired format.")
        return new_path

    def convert_wav_to_hca(self, path: str) -> str:
        temp = tempfile.NamedTemporaryFile(suffix='.hca', delete=False)
        temp.close()  # dllm windows
        self.log.debug(f"Running VGAudioCli to convert to HCA: '{path}' -> '{temp.name}'")
        output, err = external.run_vgaudio([
            path, temp.name
        ])
        if err is not None:
            self.__try_delete_file(temp.name, "temp HCA file")
            raise AudioPreprocessorError(f"VGAudioCli error:\n{err}")
        if "Success" not in output:
            self.__try_delete_file(temp.name, "temp HCA file")
            raise AudioPreprocessorError(f"VGAudioCli did not return success token, but returned: {output}")
        self.log.debug(f"VGAudioCli returned success.")
        return temp.name

    def get_hca_info(self, path: str) -> (int, int, int):
        output, err = external.run_vgaudio([
            "-m", path
        ])
        if err is not None:
            raise AudioPreprocessorError(f"VGAudioCli error:\n{err}")
        info = re.search(r"Sample count: (\d+) \((\d+.\d+) ", output)
        if info is None:
            raise AudioPreprocessorError(f"Could not obtain sample count and time in seconds from VGAudioCli")
        rate_info = re.search(r"Sample rate: (\d+) Hz", output)
        if rate_info is None:
            raise AudioPreprocessorError(f"Could not obtain sample rate from VGAudioCli")
        sample_count = int(info[1])
        length_ms = math.ceil(float(info[2]) * 1000)
        sample_rate = int(rate_info[1])
        self.log.debug(
            f"VGAudioCli says this file has {sample_count} sample(s) @ {sample_rate} Hz, duration = {length_ms}ms")
        return sample_count, sample_rate, length_ms

    def autoprocess(self, path: str) -> PreprocessResult:
        """Preprocess an audio file, or return the original path if it is valid for direct use.

        :param: path: Path to the audio file to process
        :return: the PreprocessResult
        """
        orig_filename = os.path.basename(path)
        delete_file_later = False  # Is this a temp file to delete?

        if not path.endswith(".hca"):
            self.log.debug(f"'{path}' doesn't end with .hca, so calling ffmpeg")

            # First check if it's PCM WAV and a sample rate of 48000
            # If any of these conditions fail, convert or resample as ffmpeg sees fit
            file_type, sample_rate = self.get_audio_info(path)
            if not file_type.startswith("pcm_") or sample_rate != 48000:
                self.log.info(
                    f"Resampling and/or converting '{path}' because its type is '{file_type}' with sample rate "
                    f"{sample_rate} Hz")
                path = self.resample_audio(path)
                delete_file_later = True  # mark temp WAV for deletion after converting to HCA
                self.log.debug(f"Output temporary audio path: {path}")

            # Now convert to hca and replace the path again
            hca_path = self.convert_wav_to_hca(path)
            if delete_file_later: # delete if resampled or converted earlier
                self.__try_delete_file(path, "temp WAV file")
            path = hca_path
            delete_file_later = True  # mark temp HCA for deletion later

        # at this point, the hca file path should be in path
        # now ask vgmaudio what sample rate this is and get its length in ms and sample count
        # there's no way implemented to resample hca files, so quit here if it's not 48 kHz
        self.log.debug(f"Asking VGAudioCli for info about '{path}'")
        sample_count, sample_rate, length_ms = self.get_hca_info(path)
        if sample_rate != 48000 or sample_count == -1 or length_ms == -1:
            raise AudioPreprocessorError("Sample rate error: The sample rate of explicit HCA inputs must be 48 kHz!")

        result = PreprocessResult(
            path=path,
            orig_filename=orig_filename,
            delete=delete_file_later,
            sample_count=sample_count,
            sample_rate=sample_rate,
            length_ms=length_ms)
        return result
