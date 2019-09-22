#!/usr/bin/env python
from fusesoc.capi2.generator import Generator
import os
import pathlib
import shutil
import subprocess
import tempfile

import logging
logger = logging.getLogger(__name__)

"""

This generator should be invoked by a target to generate an ipx file
locating all Qsys-Component _hw.tcl files in the fileset

"""

class QsysGenerator(Generator):
    def run(self):
        # Execute in the .cache/fusesoc generator output directory
        cwd = pathlib.Path.cwd()

        logger.warning("### Qsys_Component_Make_Ipx ###")

        rm    = os.unlink
        rm_rf = shutil.rmtree
        cp    = shutil.copy2

        #TODO cache result, don't rerun if input files haven't changed

        output_file = "components" + ".ipx"
        generator_args = ["ip-make-ipx",
                         "--source-directory=" + str(cwd),
                         "--output=" + output_file,
                         "--thorough-descent"]

        generator_cmd = ' '.join(generator_args)
        rc = subprocess.call(generator_cmd, cwd=cwd)
        if rc:
            logger.error("Generator pwd : " + str(cwd))
            logger.error("Generator command : \"" + generator_cmd  + "\"")
            logger.error("Generator exited with non-zero return code. Exiting...")
            exit(1)

        files = []
        files.append(output_file)
        self.add_files(files)

g = QsysGenerator()
g.run()
g.write()
