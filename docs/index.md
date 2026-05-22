# dtx_to_wif

Convert various kinds of weaving pattern files to WIF 1.1 files.

Conversion is done using a [terminal](#terminal-applications). If you are not comfortable using a terminal, this may not be the right package for you.

This package can also be used by weaving-related software to [read weaving pattern files into memory](#reading-files-into-memory).

## Supported formats:

dtx_to_wif can convert the following kinds of weaving design files to WIF 1.1 files:

* FiberWorks .dtx files
* TempoWeave .twa files
* WeavePoint .wpo files

It can also read WIF files into memory, including files with the standard .wif extension and also the .wifw extension (an optional extension supported by WeaveIt).

See [known limitations](#known-limitations) for some caveats.

## Converting Files

First [install](installing.md) the software.
Pay careful attention to where the `dtx_to_wif`, etc. executables are installed.
The path will be long on Windows.

Run your [terminal application](#terminal-applications).

Type the following on macOS or unix:

    dtx_to_wif path1 path2 ...

If dtx_to_wif is not found, specify the path to it, as described in [installing](installing.md).

On Windows type:

    <...path to dtx_to_wif...>\dtx_to_wif.exe path1 path2 ...

where `<...path to dtx_to_wif...>` is the path to the file, as shown when you installed `dtx_to_wif`.

The path arguments can files or directories.
All files in a directory are converted, as well as all subdirectories, sub-sub-directories, etc.

Replace "dtx" with "twa" to convert TempoWeave .twa files, or "wpo" to convert WeavePoint .wpo files.

Each new WIF file is written to the same directory as the original file with the same file name but a ".wif" extension.
If a WIF file with that path already exists, the old file is left unchanged, with a warning.
To overwrite existing files, run the command with option `--overwrite`.

If you run the command with option `-h` you will see all available options.

## Reading Files Into Memory

dtx_to_wif can read [supported](#supported-formats) weaving pattern files into memory, using function [dtx_to_wif.read_pattern_file](dtx_to_wif.pattern_reader.read_pattern_file).

The files are read into an instance of [dtx_to_wif.PatternData][dtx_to_wif.pattern_data.PatternData].
This is used by [base_loom_server](https://r-owen.github.io/base_loom_server) dobby loom control software.
It could also be used by pattern visualization software and weaving design software.

To read a weaving pattern from a file, call [dtx_to_wif.read_pattern_file][dtx_to_wif.pattern_reader.read_pattern_file]. To read a weaving pattern from a string, call [dtx_to_wif.read_pattern_data][dtx_to_wif.pattern_reader.read_pattern_data].

To write [dtx_to_wif.PatternData][dtx_to_wif.pattern_data.PatternData] to a WIF file, call [dtx_to_wif.write_wif][dtx_to_wif.wif_writer.write_wif].

## Terminal Applications

The standard terminal applications are `Terminal` for macOS, and `cmd.exe` for Windows. Other terminal applications are available, but the standard ones are fine.

## Links

* [PyPi](https://pypi.org/project/dtx-to-wif/)
* [Documentation](https://r-owen.github.io/dtx_to_wif/)
* [Source Code](https://github.com/r-owen/dtx_to_wif)
* [Issue Tracker](https://github.com/r-owen/dtx_to_wif/issues)

## Known Limitations

Known differences from the WIF files that FiberWorks writes:

* The date the dtx file was created is not written to the WIF file, since WIF has no standard location for this information.
  FiberWorks saves it as a comment in the [TEXT] section ("; Creation ...").
* The default colors and separations for warp and weft may not match.
  This is just an internal detail, as the resulting pattern is the same.
  (I have not figured out the algorithm FiberWorks uses to choose default colors and separations.)

The WeavePoint .wpo reader cannot read notes, thread thickness, nor thread separation.
Due to this limitation I consider `wpo_to_wif` only marginally useful.
However, the WeavePoint support is sufficient to allow [base_loom_server](https://pypi.org/project/base-loom-server/) to work with WeavePoint files.

## License

This software is licensed under the MIT license. See [license.txt](https://github.com/r-owen/dtx_to_wif/blob/main/license.txt) for details.
