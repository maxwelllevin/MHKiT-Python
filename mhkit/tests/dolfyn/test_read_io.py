from . import test_read_adp as tp
from . import test_read_adv as tv
from mhkit.tests.dolfyn.base import assert_allclose, save_netcdf, save_matlab, load_matlab, exdt, rfnm, drop_config
import mhkit.dolfyn.io.rdi as wh
import mhkit.dolfyn.io.nortek as awac
import mhkit.dolfyn.io.nortek2 as sig
from mhkit.dolfyn.io.api import read_example as read
import unittest
import pytest
import os

make_data = False


class io_testcase(unittest.TestCase):
    def test_save(self):
        ds = tv.dat.copy(deep=True)

        save_netcdf(ds, 'test_save')
        save_matlab(ds, 'test_save')

        assert os.path.exists(rfnm('test_save.nc'))
        assert os.path.exists(rfnm('test_save.mat'))

    def test_matlab_io(self, make_data=False):
        nens = 100
        td_vec = drop_config(read('vector_data_imu01.VEC', nens=nens))
        td_rdi_bt = drop_config(read('RDI_withBT.000', nens=nens))

        # This read should trigger a warning about the declination being
        # defined in two places (in the binary .ENX files), and in the
        # .userdata.json file. NOTE: DOLfYN defaults to using what is in
        # the .userdata.json file.
        with pytest.warns(UserWarning, match='magnetic_var_deg'):
            td_vm = drop_config(read('vmdas01_wh.ENX', nens=nens))

        if make_data:
            save_matlab(td_vec, 'dat_vec')
            save_matlab(td_rdi_bt, 'dat_rdi_bt')
            save_matlab(td_vm, 'dat_vm')
            return

        mat_vec = load_matlab('dat_vec.mat')
        mat_rdi_bt = load_matlab('dat_rdi_bt.mat')
        mat_vm = load_matlab('dat_vm.mat')

        assert_allclose(td_vec, mat_vec, atol=1e-6)
        assert_allclose(td_rdi_bt, mat_rdi_bt, atol=1e-6)
        assert_allclose(td_vm, mat_vm, atol=1e-6)

    def test_debugging(make_data=False):
        def read_txt(fname, loc):
            with open(loc(fname), 'r') as f:
                string = f.read()
            return string

        def clip_file(fname):
            log = read_txt(fname, exdt)
            newlines = [i for i, ltr in enumerate(log) if ltr == '\n']
            try:
                log = log[:newlines[100]+1]
            except:
                pass
            with open(rfnm(fname), 'w') as f:
                f.write(log)

        def read_file_and_test(fname):
            td = read_txt(fname, exdt)
            cd = read_txt(fname, rfnm)
            assert cd in td
            os.remove(exdt(fname))

        nens = 100
        drop_config(wh.read_rdi(
            exdt('RDI_withBT.000'), nens, debug_level=3))
        drop_config(awac.read_nortek(
            exdt('AWAC_test01.wpr'), nens, debug=True, do_checksum=True))
        drop_config(awac.read_nortek(
            exdt('vector_data_imu01.VEC'), nens, debug=True, do_checksum=True))
        drop_config(sig.read_signature(
            exdt('Sig500_Echo.ad2cp'), nens, rebuild_index=True, debug=True))
        os.remove(exdt('Sig500_Echo.ad2cp.index'))

        if make_data:
            clip_file('RDI_withBT.log')
            clip_file('AWAC_test01.log')
            clip_file('vector_data_imu01.log')
            clip_file('Sig500_Echo.log')
            return

        read_file_and_test('RDI_withBT.log')
        read_file_and_test('AWAC_test01.log')
        read_file_and_test('vector_data_imu01.log')
        read_file_and_test('Sig500_Echo.log')

    def test_read_warnings(self):
        with self.assertRaises(Exception):
            wh.read_rdi(exdt('H-AWAC_test01.wpr'))
        with self.assertRaises(Exception):
            awac.read_nortek(exdt('BenchFile01.ad2cp'))
        with self.assertRaises(Exception):
            sig.read_signature(exdt('AWAC_test01.wpr'))
        with self.assertRaises(IOError):
            read(rfnm('AWAC_test01.nc'))
        with self.assertRaises(Exception):
            save_netcdf(tp.dat_rdi, 'test_save.fail')
