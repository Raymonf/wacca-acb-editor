import logging
import os
import shutil
import subprocess
from typing import List

from audio.error import MissingDependencyError

ENV_VGAUDIO_DLL = "VGAUDIOCLI_DLL_PATH"
ENV_VGAUDIO_EXEC = "VGAUDIOCLI_EXEC_PATH"
ENV_FFMPEG = "FFMPEG_PATH"
ENV_DOTNET = "DOTNET_PATH"

_vgaudio_location: List[str] | None = None
_ffmpeg_location: str | None = None
_dotnet_location: str | None = None


def __get_exec_extension() -> str:
    return ".exe" if os.name == "nt" else ""


def get_dotnet_location() -> str:
    global _dotnet_location

    if _dotnet_location is not None:
        return _dotnet_location

    if ENV_DOTNET in os.environ:
        _dotnet_location = os.environ.get(ENV_DOTNET)
        return _dotnet_location

    dotnet_path = shutil.which("dotnet")
    if dotnet_path is not None:
        _dotnet_location = dotnet_path
        return _dotnet_location

    raise MissingDependencyError("dotnet could not be found; try adding it to your PATH")


def get_vgaudio_command() -> List[str]:
    global _vgaudio_location
    if _vgaudio_location is not None:
        return _vgaudio_location

    path = shutil.which("VGAudioCli")
    if path is not None:
        _vgaudio_location = path
        return _vgaudio_location

    if ENV_VGAUDIO_EXEC in os.environ:
        _vgaudio_location = [os.environ.get(ENV_VGAUDIO_EXEC)]
        return _vgaudio_location

    if ENV_VGAUDIO_DLL in os.environ:
        _vgaudio_location = [get_dotnet_location(), os.environ.get(ENV_VGAUDIO_DLL)]
        return _vgaudio_location

    if '__file__' in globals():
        dir = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../external/vgaudio")
        exec_path = dir + "/VGAudioCli" + __get_exec_extension()
        if os.path.exists(exec_path):
            _vgaudio_location = [exec_path]
            return _vgaudio_location
        dll_path = dir + "/VGAudioCli.dll"
        if os.path.exists(dll_path):
            _vgaudio_location = [get_dotnet_location(), dll_path]
            return _vgaudio_location

    raise MissingDependencyError("TODO: __file__ not defined")


def get_ffmpeg_location() -> str:
    global _ffmpeg_location

    if _ffmpeg_location is not None:
        return _ffmpeg_location

    if ENV_FFMPEG in os.environ:
        _ffmpeg_location = os.environ.get(ENV_FFMPEG)
        return _ffmpeg_location

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is not None:
        _ffmpeg_location = ffmpeg_path
        return _ffmpeg_location

    if '__file__' in globals():
        ffmpeg_path = os.path.abspath(
            os.path.dirname(os.path.abspath(__file__)) + "/../external/ffmpeg" + __get_exec_extension())
        if os.path.exists(ffmpeg_path):
            _ffmpeg_location = ffmpeg_path
            return ffmpeg_path

    raise MissingDependencyError(f"ffmpeg could not be found; try adding it in your PATH")


def run_ffmpeg(args: List[str]):
    proc = subprocess.Popen([get_ffmpeg_location()] + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = proc.communicate()
    return out.decode("utf-8") if out is not None else out, err.decode("utf-8") if err is not None else err


def run_vgaudio(args: List[str]):
    proc = subprocess.Popen(get_vgaudio_command() + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = proc.communicate()
    return out.decode("utf-8") if out is not None else out, err.decode("utf-8") if err is not None else err


def ensure_dependencies():
    has_ffmpeg = False
    try:
        get_ffmpeg_location()
        has_ffmpeg = True
    except:
        pass
    has_dotnet = False
    try:
        get_dotnet_location()
        has_dotnet = True
    except:
        pass
    has_vgaudio = False
    try:
        get_vgaudio_command()
        has_vgaudio = True
    except:
        pass

    if not has_dotnet:
        logging.error(f"dotnet could not be found! Either add it to your path or set the environment variable '{ENV_DOTNET}' to the dotnet binary.")
    if not has_ffmpeg:
        logging.error(f"ffmpeg could not be found! Either add it to your path or set the environment variable '{ENV_FFMPEG}' to the ffmpeg binary.")
    if not has_vgaudio:
        logging.error(f"ffmpeg could not be found! Either add it to your path or set the environment variable '{ENV_VGAUDIO_DLL}' to the VGAudioCli DLL or '{ENV_VGAUDIO_EXEC}' to the VGAudioCli executable binary.")
    if not has_dotnet or not has_vgaudio or not has_ffmpeg:
        raise MissingDependencyError(f"Dependency check failed! (vgaudio: {has_vgaudio}, ffmpeg: {has_ffmpeg}, dotnet: {has_dotnet})")
