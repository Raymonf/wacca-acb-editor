from collections import OrderedDict
from io import BytesIO
import pathlib
import argparse
import subprocess
import sys
import json

from atom_types.runtime.acb import Acb

try:
    from construct import *
    from construct.core import *
except ImportError:
    # Call pip to install deps
    print("Installing dependencies...", end='')
    subprocess.check_call([sys.executable] + "-m pip -q install construct".split(" "))
    from construct import *
    from construct.core import *
    from openpyxl import Workbook, load_workbook
    print(" done.")
    
from atom_types.file.awb_file import Awb_File as Awb_File
from atom_types.file.utf_file import Utf_File as Utf_File
from atom_types.runtime.utf import Utf, UtfBlob

parser = argparse.ArgumentParser()

# Credit to https://stackoverflow.com/a/51675877
class SkipFilter(object):

    def __init__(self, types=None, keys=None, allow_empty=False):
        self.types = tuple(types or [])
        self.keys = set(keys or [])
        self.allow_empty = allow_empty  # if True include empty filtered structures

    def filter(self, data): #, path=""):
        if isinstance(data, str):
            return data
        elif isinstance(data, bool):
            return int(data)
        elif hasattr(data, 'decode'):
            return data
        elif isinstance(data, collections.abc.Mapping):
            result = OrderedDict()  # dict-like, use dict as a base
            for k, v in data.items():
                if k == "data" and "value" in data:
                    continue
                if True in [k.startswith(key) for key in self.keys] or isinstance(v, self.types):  # skip key/type
                    continue
                try:
                    result[k] = self.filter(v) #, path=f"{path}{k}/")
                except ValueError:
                    pass
            if result or self.allow_empty:
                return result
        elif isinstance(data, collections.abc.Sequence):
            result = []  # a sequence, use list as a base
            for i, v in enumerate(data):
                if isinstance(v, self.types):  # skip type
                    continue
                try:
                    result.append(self.filter(v)) #, path=f"{path}[{i}]/"))
                except ValueError:
                    pass
            if result or self.allow_empty:
                return result
        else:  # we don't know how to traverse this structure...
            return data  # return it as-is, hope for the best...
        raise ValueError

class DataFilter(object):
    def filter(self, data): #, path=""):
        if isinstance(data, str):
            return data
        elif isinstance(data, bool):
            return int(data)
        elif hasattr(data, 'decode'):
            return data
        if isinstance(data, collections.abc.Mapping):
            result = OrderedDict()  # dict-like, use dict as a base            
            for k, v in data.items():
                if k == "data" and "value" in data.keys():
                    continue
                elif k.startswith("_"):
                    continue
                try:
                    result[k] = self.filter(v) #, path=f"{path}{k}/")
                except ValueError:
                    pass
            return data
        elif isinstance(data, collections.abc.Sequence):
            result = []  # a sequence, use list as a base
            for _, v in enumerate(data):
                try:
                    result.append(self.filter(v)) #, path=f"{path}[{i}]/"))
                except ValueError:
                    pass
            if result:
                return result
        else:  # we don't know how to traverse this structure...
            return data  # return it as-is, hope for the best...

def export_awb(args):
    jsonPath = pathlib.Path(args.json)
    # if jsonPath.exists():
    #     response = input(f"File {jsonPath.name} exists. Overwrite [y/N]? ")
    #     if (response.lower() != 'y'):
    #         return

    # Fail fast if the file is in use
    with open(args.json, "wb") as _:
        pass

    awb_in = Awb_File.parse_stream(args.input)
    def a(): Pass
    preprocessor = SkipFilter([io.BytesIO, bytes, type(a)], ["_","offset1","offset2","length"], allow_empty=True)
    filtered = preprocessor.filter(awb_in)
    with open(jsonPath.with_suffix(".json"), "w") as json_out:
        json.dump(filtered, json_out, indent=4, ensure_ascii=False)
    Debugger(Awb_File).build_file(awb_in, args.rebuild)

def export_acb(args):
    jsonPath = pathlib.Path(args.json)
    # Fail fast if the file is in use
    with open(args.json, "wb") as _:
        pass

    acb_in = Acb.parse_stream(pathlib.Path(args.input.name).parent, args.input)
    preprocessor = SkipFilter([io.BytesIO, bytes], ["_","offset1","offset2","length"], allow_empty=True)
    data_remover = SkipFilter([], "_", allow_empty=True)
    # print(acb_in["header"]["magic"])
    data_removed = data_remover.filter(acb_in.utf.tree)
    # print(data_removed["header"]["magic"])
    # Utf_File.build_file(acb_in.tree, args.rebuild)
    # print(acb_in.get(0, "WaveformExtensionDataTable").read())
    # acb_in.add_row(acb_in.rows[0])
    with open(args.rebuild, "wb") as out:
        acb_in.build_stream(out)
        
    filtered = preprocessor.filter(acb_in.utf.tree)
    with open(jsonPath.with_suffix(".json"), "w") as json_out:
        json.dump(filtered, json_out, indent=4, ensure_ascii=False)

def normalize_input_type(target, input):
    if isinstance(target, (EnumInteger, EnumIntegerString)):
        try:
            return int(input)
        except ValueError:
            return str(input)
    elif isinstance(target, int):
        return int(input)
    return input

def main():
    subparsers = parser.add_subparsers(title='subcommands',
                                    description='valid subcommands',
                                    help='additional help')
    parsers = {}
    for subcommand, func in [
                ("awb", export_awb),
                ("acb", export_acb)
            ]:
        parsers[subcommand] = subparsers.add_parser(subcommand, help=f'{subcommand} help')
        p = parsers[subcommand]

        p.add_argument('input', type=argparse.FileType('rb', 0))
        p.add_argument('rebuild')
        p.add_argument('json')
        p.set_defaults(func=func)

    parser.set_defaults(func=lambda _: parser.print_help())
    args = parser.parse_args()
    args.func(args)
    
if __name__=="__main__":
   main()