Convert weaving pattern files to WIF 1.1

This package provides:

* Command-line utilities to batch-convert weaving design files to WIF 1.1:

    * `dtx_to_wif` converts Fiberworks .dtx files.
    * `twa_to_wif` converts TempoWeave .twa files.
    * `wpo_to_wif` converts WeavePoint .wpo files, though some information is lost.

* Command-line utility `diff_weaving` shows the differences between two weaving pattern files.

* Python library code can read a weaving pattern file into memory. One use is for dobby loom drivers, such as [base_loom_server](https://r-owen.github.io/base_loom_server/).

Links:

* [Documentation](https://r-owen.github.io/dtx_to_wif/)
* [Source Code](https://github.com/r-owen/dtx_to_wif/)
* [PyPI](https://pypi.org/project/dtx-to-wif/)

This software is licensed under the MIT license; see license.txt for details.
