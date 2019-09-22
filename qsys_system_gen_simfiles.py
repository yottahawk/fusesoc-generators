#!/usr/bin/env python
from fusesoc.capi2.generator import Generator
import os
import pathlib
import shutil
import subprocess
import tempfile

import logging
logger = logging.getLogger(__name__)

class QsysGenerator(Generator):
    def run(self):
        # Execute in the .cache/fusesoc generator output directory
        cwd = pathlib.Path.cwd()

        qsys_file_files_root = pathlib.Path(self.files_root) / pathlib.Path(self.config.get('qsys_file')).resolve()
        qsys_file_cache = (cwd / qsys_file_files_root.name).resolve()

        rm    = os.unlink
        rm_rf = shutil.rmtree
        cp    = shutil.copy2

        # Copy the qsys file to the .cache/fusesoc directory
        # This is required becuase the .sopcinfo file is always generated in the same
        # directory as the .qsys file (why? I do not know...)
        if qsys_file_cache.exists():
            rm(str(qsys_file_cache))
        cp(str(qsys_file_files_root), str(qsys_file_cache))

        # Here we can consider a way to 'cache' the output of the qsys-generate process, only
        # updating if one of our input files has changed.
        output_dir = cwd / 'output_files'
        # if output_dir.exists():
        #     rm_rf(str(cwd / 'output_files'))

        # Each .core component which contains qsys-components (_hw.tcl files) should
        # generate a .ipx file, and pass the parent directory into this generator.
        ipx_files = []
        for file in self.input_files:
            if pathlib.Path(file).suffix == '.ipx':
                ipx_files.append(file)

        generator_args = ["qsys-generate",
                         str(qsys_file_cache),
                         "--synthesis=VHDL",
                         "--search-path=" + ','.join(str(i) for i in ipx_files) + ',$',
                         "--output-directory=output_files"]

        generator_cmd = ' '.join(generator_args)
        rc = subprocess.call(generator_cmd, cwd=cwd)
        if rc:
            logger.error("Generator pwd : " + str(cwd))
            logger.error("Generator command : \"" + generator_cmd  + "\"")
            logger.error("Generator exited with non-zero return code. Exiting...")
            exit(1)

        # For qsys-synthesis, the only files required are the .qip, and all generated submodule files.
        # We need to preserve the relative paths between the .qip and all submodule files, since it
        # references them using relative paths.
        # For synthesis, only the .qip needs to be added to the Quartus project, so all the other files
        # can be attributed as 'include_only'. For simulation, we may need to add these submodule files
        # into a simulation script.

        sys_name = qsys_file_cache.stem
        # .qip file
        files = []
        files.append(str(pathlib.Path('output_files/synthesis/' + sys_name + '.qip')))
        self.add_files(files, fileset='qsys_qip', file_type='QIP')
        # top-level .vhd file + other .vhd files placed here... (why?)
        files = []
        file_path = str(pathlib.Path('output_files/synthesis/*' + '.vhd'))
        file_dict = {file_path : {'is_include_file' : True}}
        files.append(file_dict)
        # submodule files
        exts = ['.vhd','.v','.sv','.iv','.c','.h','.tcl','.sdc','.mif','.hex']
        for ext in exts:
            file_path = str(pathlib.Path('output_files/synthesis/submodules/*' + ext))
            file_dict = {file_path : {'is_include_file' : True}}
            files.append(file_dict)
        self.add_files(files, fileset='qsys_synthesis', file_type='USER')

g = QsysGenerator()
g.run()
g.write()
