import os
import json
import re

from avocado import Test
from avocado import main
from avocado.utils import archive
from avocado.utils import process
from avocado.utils import build
from avocado.utils.software_manager import SoftwareManager


class Ebizzy(Test):

    '''
    ebizzy is designed to generate a workload resembling common web application
    server workloads. It is highly threaded, has a large in-memory working set,
    and allocates and deallocates memory frequently.
    '''

    def setUp(self):
        '''
        Build ebizzy
        Source:
        http://liquidtelecom.dl.sourceforge.net/project/ebizzy/ebizzy/0.3
        /ebizzy-0.3.tar.gz
        '''
        sm = SoftwareManager()
        if not sm.check_installed("gcc") and not sm.install("gcc"):
            self.error("Gcc is needed for the test to be run")
        tarball = self.fetch_asset('http://liquidtelecom.dl.sourceforge.net'
                                   '/project/ebizzy/ebizzy/0.3'
                                   '/ebizzy-0.3.tar.gz')
        data_dir = os.path.abspath(self.datadir)
        archive.extract(tarball, self.srcdir)
        version = os.path.basename(tarball.split('.tar.')[0])
        self.srcdir = os.path.join(self.srcdir, version)

        patch = self.params.get(
            'patch', default='Fix-build-issues-with-ebizzy.patch')
        os.chdir(self.srcdir)
        p1 = 'patch -p0 < %s/%s' % (data_dir, patch)
        process.run(p1, shell=True)
        process.run('[ -x configure ] && ./configure', shell=True)
        build.make(self.srcdir)

    # Note: default we use always mmap()
    def test(self):

        args = self.params.get('args', default='')
        num_chunks = self.params.get('num_chunks', default=1000)
        chunk_size = self.params.get('chunk_size', default=512000)
        seconds = self.params.get('seconds', default=100)
        num_threads = self.params.get('num_threads', default=100)
        logfile = os.path.join(self.outputdir, 'ebizzy.log')
        args2 = '-m -n %s -P -R -s %s -S %s -t %s' % (num_chunks, chunk_size,
                                                      seconds, num_threads)
        args = args + ' ' + args2

        results = process.system_output('%s/ebizzy %s' % (self.srcdir, args))
        pattern = re.compile(r"(.*?) records/s")
        records = pattern.findall(results)[0]
        pattern = re.compile(r"real (.*?) s")
        real = pattern.findall(results)[0]
        pattern = re.compile(r"user (.*?) s")
        usr_time = pattern.findall(results)[0]
        pattern = re.compile(r"sys (.*?) s")
        sys_time = pattern.findall(results)[0]

        perf_json = {'records': records, 'real_time':
                     real, 'user': usr_time, 'sys': sys_time}
        output_path = os.path.join(self.outputdir, "perf.json")
        json.dump(perf_json, open(output_path, "w"))

if __name__ == "__main__":
    main()
