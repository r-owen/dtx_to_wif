# Installing

1. Check if you have Python 3.10 or newer installed.

    Run your [terminal application](index.md/#terminal-applications).

    At the prompt type:

        python --version
    
    If Python is installed, this will print a version number.
    If that version number is at least 3.10, you may skip the next step
    (though you might wish to upgrade your Python in any case).

2. If necessary, install [Python](https://www.python.org/downloads/) 3.10 or later, preferably the current release.

    The link has installers for common operating systems.
    However, on Windows you may want to try Microsoft's app store.

3. Install this dtx_to_wif package.

        python -m pip install dtx_to_wif

    Watch the output carefully.
    Near the end, pip should tell you where it installed executables `dtx_to_wif` and `wpo_to_wif`.
    On Windows these will have extension ".exe", and they will probably be deeply buried.
    Record this information so you can find it later!

4. Test your installation.

    On macOS or linux try the following first:

        dtx_to_wif -h
    
    This should run the application and print some help.
    If it does not, specify the full path:

        path-to-executable/dtx_to_wif -h
    
    If that is necessary, consider adding the directory containing dtx_to_wif to your PATH, or creating aliases for the dtx_to_wif and wpo_to_wif executables.
    Describing how is out of scope for this document, but instructions are widely available.

    On Windows type the following (note the ".exe" suffix):

        path-to-executable\dtx_to_wif.exe -h

5. To upgrade to a newer version of `dtx_to_wif`:

        python -m pip install --upgrade dtx_to_wif

    You can also specify a specific version; seee pip's documentation for details.

## Developer Info

To install the package in a locally editable form:

* Fork the project and clone that to a local folder.

* Install an editable version of the package. From within the dtx_to_wif folder:

    python -m pip install -e ".[dev]"

* Run unit tests:

    python -m unittest tests/test_*.py
