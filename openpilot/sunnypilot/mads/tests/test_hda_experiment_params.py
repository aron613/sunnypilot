"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from unittest.mock import MagicMock

from opendbc.car import structs
from opendbc.sunnypilot.car.hyundai.values import HyundaiFlagsSP
from openpilot.sunnypilot.mads.helpers import set_hyundai_hda_suppression_experiment
from openpilot.common.test import OpenpilotTestCase

A = HyundaiFlagsSP.CANFD_HDA_EXP_LFA_STATUS.value
B = HyundaiFlagsSP.CANFD_HDA_EXP_LANE_BYTES.value


def params_with(value):
  params = MagicMock()
  params.get = MagicMock(return_value=value)
  return params


def cp_sp(lx3=True):
  c = structs.CarParamsSP()
  if lx3:
    c.flags |= HyundaiFlagsSP.CANFD_ADRV_LATERAL_TAKEOVER.value
  return c


class TestHdaSuppressionExperimentParam(OpenpilotTestCase):
  def test_mapping(self):
    for value, expected_flags in ((0, 0), (1, A), (2, B), (3, A | B)):
      c = cp_sp()
      assert set_hyundai_hda_suppression_experiment(c, params_with(value)) == value
      assert c.flags & (A | B) == expected_flags, value
      assert c.hdaSuppressionExperiment == value

  def test_default_and_garbage_are_off(self):
    for value in (None, "", "9", 7, -1, "x"):
      c = cp_sp()
      assert set_hyundai_hda_suppression_experiment(c, params_with(value)) == 0, value
      assert c.flags & (A | B) == 0
      assert c.hdaSuppressionExperiment == 0

  def test_other_cars_ignore_the_param(self):
    c = cp_sp(lx3=False)
    assert set_hyundai_hda_suppression_experiment(c, params_with(3)) == 0
    assert c.flags == 0
    assert c.hdaSuppressionExperiment == 0
