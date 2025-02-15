from gemlog.core import *
from gemlog.core import _convert_one_file
import pytest
import shutil, os

def setup_module():
    try:
        shutil.rmtree('tmp') # exception if the directory doesn't exist
    except:
        pass
    os.makedirs('tmp')
    os.chdir('tmp')
    
def teardown_module():
    os.chdir('..')
    shutil.rmtree('tmp') 


def test_read_gem_missing():
    with pytest.raises(MissingRawFiles):
        read_gem(nums = np.arange(10, 20), path = '../data', SN = '000') # test missing files

def test_read_gem_empty():
    with pytest.raises(MissingRawFiles):
        read_gem(nums = np.arange(5), path = '../data', SN = '000') # test purely empty files

def test_read_gem_edge_cases():
    #print(os.getcwd())
    # test a malformed file
    with pytest.raises(CorruptRawFile):
        read_gem(nums = np.array([23]), path = '../data', SN = '096') 

    # test a differently-malformed file
    with pytest.raises(CorruptRawFileInadequateGPS):
        read_gem(nums = np.array([7]), path = '../data/test_data', SN = '138') 

    # test a mix of files with no gps, one gps line (that used to trigger a divide by zero warning), inadequate gps data, and normal gps data
    L = read_gem('../data/incomplete_gps_test_data/', SN = '179')
    assert all((L['header'].drift_deg0 > 0) == np.array([False, False, True, False, True, False]))
    assert len(L['data']) == 2

    
    
def test_read_gem_good_data():
    ## read_gem always reads files in one block, so no sense in testing 25 files
    read_gem(nums = np.arange(3), path =  '../demo_missing_gps/raw_with_gps', SN = '077') # test good data


## Convert tests: ensure that it doesn't crash, and that the output mseed file is identical to a reference
def test_Convert_good_data():
    convert('../demo_missing_gps/raw_with_gps', SN = '077', convertedpath = 'test_output_mseed', output_format = 'wav', file_length_hour = 1)
    convert('../demo_missing_gps/raw_with_gps', SN = '077', convertedpath = 'test_output_mseed', output_format = 'sac', file_length_hour = 1)
    convert('../demo_missing_gps/raw_with_gps', SN = '077', convertedpath = 'test_output_mseed', file_length_hour = 1)
    output = obspy.read('test_output_mseed/2020-04-24T22_00_00..077..HDF.mseed')[0]
    reference = obspy.read('../demo_missing_gps/converted_with_gps/2020-04-24T22_00_00..077..HDF.mseed')[0]
    #reference.stats.starttime += 0.01 ## correction
    t1 = output.stats.starttime + 100
    t2 = output.stats.endtime - 100
    output.trim(t1, t2)
    reference.trim(t1, t2)
    #assert output.__eq__(reference)
    assert np.std(output.data - reference.data) < 0.1 # counts

## check that v1.10 data files are read to be identical to corresponding v0.91 files
def test_v1_10_v0_91_read_gem():
    x = read_gem(path = '../data/v1.10/', SN = '210')
    y = read_gem(path = '../data/v0.91/', SN = '210')
    assert x['data'].__eq__(y['data'])

## On further thought, this shouldn't run without errors; it should fail because any step means uncertainty about which data is correct. So don't run this. See test_step_detection instead.
#def test_convert_edge_cases():
#    # test a raw file where a leap second change happens very early, triggering a GPS break with no good GPS data before it
#    # this just needs to run without crashing
#    convert('../data/test_data/early_leap_second/', SN = '232', convertedpath = 'test_output_mseed')

def test_read_no_gps():
    ## ensure that the right exceptions are raised with files with gps issues
    ## FILE0169 has no gps; FILE0170 has inadequate GPS
    ## read_gem reads many files, so it can't tell the difference between no GPS and inadequate GPS
    with pytest.raises(CorruptRawFileInadequateGPS): 
        L = read_gem(path='../data/incomplete_gps_test_data', nums = [169], SN = '179', require_gps = True)
    with pytest.raises(CorruptRawFileInadequateGPS):
        L = read_gem(path='../data/incomplete_gps_test_data', nums = [170], SN = '179', require_gps = True)
    with pytest.raises(CorruptRawFileInadequateGPS):
        L = read_gem(path='../data/incomplete_gps_test_data', nums = [169,170], SN = '179', require_gps = True)

    ## test the same files, with require_gps False
    L = read_gem(path='../data/incomplete_gps_test_data', nums = [169], SN = '179', require_gps = False)
    L = read_gem(path='../data/incomplete_gps_test_data', nums = [170], SN = '179', require_gps = False)

    ## test convert_one_file with require_gps = False (should work)
    _convert_one_file('../data/incomplete_gps_test_data/FILE0169.179', require_gps = False)
    _convert_one_file('../data/incomplete_gps_test_data/FILE0170.179', require_gps = False)

    ## test convert_one_file with require_gps = True (should raise exception)
    with pytest.raises(CorruptRawFile):
        _convert_one_file('../data/incomplete_gps_test_data/FILE0169.179', require_gps = True)
    with pytest.raises(CorruptRawFile):
        _convert_one_file('../data/incomplete_gps_test_data/FILE0170.179', require_gps = True)
