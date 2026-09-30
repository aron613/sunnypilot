"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from unittest.mock import MagicMock

from opendbc.car import structs
from opendbc.sunnypilot.car.hyundai.values import HyundaiFlagsSP
from openpilot.sunnypilot.mads.helpers import set_hyundai_hda_suppression_experiment, set_hyundai_auto_suppress_hda
from openpilot.common.test import OpenpilotTestCase

A = HyundaiFlagsSP.CANFD_HDA_EXP_LFA_STATUS.value


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
    for value, expected, expected_flags in ((0, 0, 0), (1, 1, A), (2, 0, 0), (3, 0, 0)):
      c = cp_sp()
      assert set_hyundai_hda_suppression_experiment(c, params_with(value)) == expected
      assert c.flags & A == expected_flags, value
      assert c.hdaSuppressionExperiment == expected

  def test_default_and_garbage_are_off(self):
    for value in (None, "", "9", 7, -1, "x"):
      c = cp_sp()
      assert set_hyundai_hda_suppression_experiment(c, params_with(value)) == 0, value
      assert c.flags & A == 0
      assert c.hdaSuppressionExperiment == 0

  def test_other_cars_ignore_the_param(self):
    c = cp_sp(lx3=False)
    assert set_hyundai_hda_suppression_experiment(c, params_with(3)) == 0
    assert c.flags == 0
    assert c.hdaSuppressionExperiment == 0


B = HyundaiFlagsSP.CANFD_AUTO_SUPPRESS_HDA.value


def params_bool(value):
  params = MagicMock()
  params.get_bool = MagicMock(return_value=value)
  return params


class TestAutoSuppressHdaParam(OpenpilotTestCase):
  def test_off_by_default(self):
    c = cp_sp()
    assert set_hyundai_auto_suppress_hda(c, params_bool(False)) is False
    assert c.flags & B == 0

  def test_on_sets_the_flag(self):
    c = cp_sp()
    assert set_hyundai_auto_suppress_hda(c, params_bool(True)) is True
    assert c.flags & B == B

  def test_other_cars_never_get_it(self):
    c = cp_sp(lx3=False)
    assert set_hyundai_auto_suppress_hda(c, params_bool(True)) is False
    assert c.flags & B == 0
