from datetime import datetime
import kachery_client as kc
import os
import pathlib
import pynwb
import pytz
import uuid


def test_1():
    print("In test_1, os.environ['NWB_DATAJOINT_BASE_DIR'] is", os.environ['NWB_DATAJOINT_BASE_DIR'])
    raw_dir = pathlib.Path(os.environ['NWB_DATAJOINT_BASE_DIR']) / 'raw'
    nwbfile_path = raw_dir / 'test.nwb'

    from nwb_datajoint.common import Session, DataAcquisitionDevice, CameraDevice, Probe
    from nwb_datajoint.data_import import insert_sessions

    with kc.config(fr='default_readonly'):
        kc.load_file('sha1://8ed68285c327b3766402ee75730d87994ac87e87/beans20190718_no_eseries_no_behavior.nwb',
                     dest=str(nwbfile_path))

    # test that the file can be read. this is not used otherwise
    with pynwb.NWBHDF5IO(path=str(nwbfile_path), mode='r', load_namespaces=True) as io:
        nwbfile = io.read()
        assert nwbfile is not None

    insert_sessions(nwbfile_path.name)

    x = (Session() & {'nwb_file_name': 'test_.nwb'}).fetch1()
    assert x['nwb_file_name'] == 'test_.nwb'
    assert x['subject_id'] == 'Beans'
    assert x['institution_name'] == 'University of California, San Francisco'
    assert x['lab_name'] == 'Loren Frank'
    assert x['session_id'] == 'beans_01'
    assert x['session_description'] == 'Reinforcement leaarning'
    assert x['session_start_time'] == datetime(2019, 7, 18, 15, 29, 47)
    assert x['timestamps_reference_time'] == datetime(1970, 1, 1, 0, 0)
    assert x['experiment_description'] == 'Reinforcement learning'

    x = DataAcquisitionDevice().fetch()
    # TODO No data acquisition devices?
    assert len(x) == 0

    x = CameraDevice().fetch()
    # TODO No camera devices?
    assert len(x) == 0

    x = Probe().fetch()
    assert len(x) == 1
    assert x[0]['probe_type'] == '128c-4s8mm6cm-20um-40um-sl'
    assert x[0]['probe_description'] == '128 channel polyimide probe'
    assert x[0]['num_shanks'] == 4
    assert x[0]['contact_side_numbering'] == 'True'


# This is how I created the file: beans20190718_no_eseries_no_behavior.nwb
def _create_beans20190718_no_eseries_no_behavior():
    # Use: pip install git+https://github.com/flatironinstitute/h5_to_json
    import h5_to_json as h5j

    basepath = '/workspaces/nwb_datajoint/devel/data/nwb_builder_test_data/'
    nwb_path = basepath + '/beans20190718.nwb'
    x = h5j.h5_to_dict(
        nwb_path,
        exclude_groups=['/acquisition/e-series', '/processing/behavior'],
        include_datasets=True
    )
    h5j.dict_to_h5(x, basepath + '/beans20190718_no_eseries_no_behavior.nwb')


def _old_method_for_creating_test_file():
    nwb_content = pynwb.NWBFile(
        session_description='test-session-description',
        experimenter='test-experimenter-name',
        lab='test-lab',
        institution='test-institution',
        session_start_time=datetime.now(),
        timestamps_reference_time=datetime.fromtimestamp(0, pytz.utc),
        identifier=str(uuid.uuid1()),
        session_id='test-session-id',
        notes='test-notes',
        experiment_description='test-experiment-description',
        subject=pynwb.file.Subject(
            description='test-subject-description',
            genotype='test-subject-genotype',
            sex='female',
            species='test-subject-species',
            subject_id='test-subject-id',
            weight='2 lbs'
        ),
    )
    nwb_content.add_epoch(
        start_time=float(0),   # start time in seconds
        stop_time=float(100),  # end time in seconds
        tags='epoch1'
    )

    nwb_content.create_device(
        name='test-device'
    )
    nwb_content.create_electrode_group(
        name='test-electrode-group',
        location='test-electrode-group-location',
        device=nwb_content.devices['test-device'],
        description='test-electrode-group-description'
    )
    num_channels = 8
    for m in range(num_channels):
        location = [0, m]
        grp = nwb_content.electrode_groups['test-electrode-group']
        impedance = -1.0
        nwb_content.add_electrode(
            id=m,
            x=float(location[0]), y=float(location[1]), z=float(0),
            imp=impedance,
            location='test-electrode-group-location',
            filtering='none',
            group=grp
        )
    nwb_fname = os.environ['NWB_DATAJOINT_BASE_DIR'] + '/test.nwb'
    with pynwb.NWBHDF5IO(path=nwb_fname, mode='w') as io:
        io.write(nwb_content)
        io.close()
