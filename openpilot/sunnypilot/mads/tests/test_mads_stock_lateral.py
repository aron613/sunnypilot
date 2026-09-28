"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from openpilot.cereal import custom
from opendbc.car import structs
from openpilot.sunnypilot.mads.helpers import MadsSteeringModeOnBrake
from openpilot.sunnypilot.mads.tests.test_mads_steering_mode import make_mads, make_car_state
from openpilot.common.test import OpenpilotTestCase

EventNameSP = custom.OnroadEventSP.EventName
ButtonType = structs.CarState.ButtonEvent.Type


def car_state_sp(stock_lateral_active, hda_road_active=False, lfa_off_requested=False, lfa_off_failed=False):
  cs_sp = structs.CarStateSP()
  cs_sp.stockLateralActive = stock_lateral_active
  cs_sp.hdaRoadActive = hda_road_active
  cs_sp.stockLfaOffRequested = lfa_off_requested
  cs_sp.stockLfaOffFailed = lfa_off_failed
  return cs_sp


def press_lkas(cs):
  be = structs.CarState.ButtonEvent()
  be.type = ButtonType.lkas
  be.pressed = True
  cs.buttonEvents = [be]
  return cs


class TestMadsStockLateral(OpenpilotTestCase):
  def setup_method(self):
    mocker = self._fixture("mocker")
    self.mads, self.sd = make_mads(mocker, MadsSteeringModeOnBrake.REMAIN_ACTIVE)

  def test_stock_lateral_raises_event_and_pauses(self):
    self.mads.enabled = True
    self.mads.update(make_car_state(v_ego=10.0), car_state_sp(True))
    assert self.sd.events_sp.has(EventNameSP.stockLateralActive)
    assert self.sd.events_sp.has(EventNameSP.silentLkasDisable)

  def test_stock_lateral_event_absent_when_clear(self):
    self.mads.enabled = True
    self.mads.update(make_car_state(v_ego=10.0), car_state_sp(False))
    assert not self.sd.events_sp.has(EventNameSP.stockLateralActive)
    assert not self.sd.events_sp.has(EventNameSP.silentLkasDisable)

  def test_lkas_press_while_stock_lateral_is_refused_without_state_change(self):
    for mads_enabled in (True, False):
      for selfdrive_enabled in (True, False):
        self.mads.enabled = mads_enabled
        self.sd.enabled = selfdrive_enabled
        self.sd.events.clear()
        self.sd.events_sp.clear()
        self.mads.update(press_lkas(make_car_state(v_ego=10.0)), car_state_sp(True))
        assert self.sd.events_sp.has(EventNameSP.lkasBlockedByStockLateral), (mads_enabled, selfdrive_enabled)
        # none of the normal button outcomes
        assert not self.sd.events_sp.has(EventNameSP.lkasEnable)
        assert not self.sd.events_sp.has(EventNameSP.lkasDisable)
        assert not self.sd.events_sp.has(EventNameSP.manualSteeringRequired)

  def test_hda_road_raises_event_and_pauses(self):
    self.mads.enabled = True
    self.mads.update(make_car_state(v_ego=10.0), car_state_sp(False, hda_road_active=True))
    assert self.sd.events_sp.has(EventNameSP.hdaRoadLateral)
    assert not self.sd.events_sp.has(EventNameSP.stockLateralActive)
    assert self.sd.events_sp.has(EventNameSP.silentLkasDisable)

  def test_lkas_press_while_hda_road_changes_no_state_and_is_not_refused(self):
    # the car side turns the press into an LFA-off request to the ADAS ECU and raises its own alert, so MADS must not
    # add the refusal here, and must not toggle either
    for selfdrive_enabled in (True, False):
      self.mads.enabled = True
      self.sd.enabled = selfdrive_enabled
      self.sd.events.clear()
      self.sd.events_sp.clear()
      self.mads.update(press_lkas(make_car_state(v_ego=10.0)), car_state_sp(False, hda_road_active=True))
      assert not self.sd.events_sp.has(EventNameSP.lkasBlockedByStockLateral), selfdrive_enabled
      assert not self.sd.events_sp.has(EventNameSP.manualSteeringRequired)
      assert not self.sd.events_sp.has(EventNameSP.lkasDisable)
      assert not self.sd.events_sp.has(EventNameSP.lkasEnable)

  def test_stock_lfa_off_request_and_failure_alerts(self):
    self.mads.enabled = True
    self.mads.update(make_car_state(v_ego=10.0), car_state_sp(False, hda_road_active=True, lfa_off_requested=True))
    assert self.sd.events_sp.has(EventNameSP.requestingStockLfaOff)
    assert not self.sd.events_sp.has(EventNameSP.stockLfaOffFailed)
    self.sd.events_sp.clear()
    self.mads.update(make_car_state(v_ego=10.0), car_state_sp(False, hda_road_active=True, lfa_off_failed=True))
    assert self.sd.events_sp.has(EventNameSP.stockLfaOffFailed)
    assert not self.sd.events_sp.has(EventNameSP.requestingStockLfaOff)
    self.sd.events_sp.clear()
    self.mads.update(make_car_state(v_ego=10.0), car_state_sp(False))
    assert not self.sd.events_sp.has(EventNameSP.requestingStockLfaOff)
    assert not self.sd.events_sp.has(EventNameSP.stockLfaOffFailed)

  def test_lkas_press_without_stock_lateral_still_toggles(self):
    self.mads.enabled = False
    self.sd.enabled = False
    self.mads.update(press_lkas(make_car_state(v_ego=10.0)), car_state_sp(False))
    assert self.sd.events_sp.has(EventNameSP.lkasEnable)
    assert not self.sd.events_sp.has(EventNameSP.lkasBlockedByStockLateral)
