# #############################################################################
# loc_xform_test.py
#
"""
Basic unit-test for LOC encode / decode Python methods.
"""

# #############################################################################
import loc.loc_xform as xform

# #############################################################################
# Setup some variables pointing to diff dir/sub-dir full-paths.

# #############################################################################
def test_loc_encode():
    """
    Cross-check LOC-encoded value for few hard-coded inputs.
    """
    assert 65541 == xform.loc_encode(1, 5)
    assert 131089 == xform.loc_encode(2, 17)

# #############################################################################
def test_loc_decode():
    """
    Cross-check LOC-decoded value for few hard-coded inputs.
    """
    assert (1, 5) == xform.loc_decode(65541)
    assert (2, 17) == xform.loc_decode(131089)

# #############################################################################
def test_loc_encode_decode_roundtrip():
    """
    Cross-check LOC-encoding / decoding roundtrip.
    """
    (file_index, line_num) = xform.loc_decode(65541)
    assert xform.loc_encode(file_index, line_num) == 65541
