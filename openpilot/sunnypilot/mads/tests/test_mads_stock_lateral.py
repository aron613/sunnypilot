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


def car_state_sp(stock_lateral_active, hda_road_active=False, lfa_off_requested=False, lfa_off_failed=False,
                 auto_suppressing=False, auto_suppress_failed=False):
  cs_sp = structs.CarStateSP()
  cs_sp.stockLateralActive = stock_lateral_active
  cs_sp.hdaRoadActive = hda_road_active
  cs_sp.stockLfaOffRequested = lfa_off_requested
  cs_sp.stockLfaOffFailed = lfa_off_failed
  cs_sp.stockLfaAutoSuppressing = auto_suppressing
  cs_sp.stockLfaAutoSuppressFailed = auto_suppress_failed
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

  def test_auto_suppress_alerts(self):
    self.mads.enabled = True
    self.mads.update(make_car_state(v_ego=10.0), car_state_sp(False, hda_road_active=True, auto_suppressing=True))
    assert self.sd.events_sp.has(EventNameSP.suppressingStockLfa)
    assert not self.sd.events_sp.has(EventNameSP.stockHdaHasSteering)
    assert not self.sd.events_sp.has(EventNameSP.requestingStockLfaOff)
    self.sd.events_sp.clear()
    self.mads.update(make_car_state(v_ego=10.0), car_state_sp(False, hda_road_active=True, auto_suppress_failed=True))
    assert self.sd.events_sp.has(EventNameSP.stockHdaHasSteering)
    assert not self.sd.events_sp.has(EventNameSP.suppressingStockLfa)
    self.sd.events_sp.clear()
    self.mads.update(make_car_state(v_ego=10.0), car_state_sp(False))
    assert not self.sd.events_sp.has(EventNameSP.suppressingStockLfa)
    assert not self.sd.events_sp.has(EventNameSP.stockHdaHasSteering)

  def test_lkas_press_without_stock_lateral_still_toggles(self):
    self.mads.enabled = False
    self.sd.enabled = False
    self.mads.update(press_lkas(make_car_state(v_ego=10.0)), car_state_sp(False))
    assert self.sd.events_sp.has(EventNameSP.lkasEnable)
    assert not self.sd.events_sp.has(EventNameSP.lkasBlockedByStockLateral)


def cruise_available(available):
  cs = make_car_state(v_ego=10.0)
  cs.cruiseState.available = available
  return cs


class TestMadsLateralSurvivesMainOff(OpenpilotTestCase):
  """LX3 behavior, not an option: cruise engages both, but turning cruise main off leaves lateral engaged and the LFA
  button is what switches it off"""
  def setup_method(self):
    mocker = self._fixture("mocker")
    self.mads, self.sd = make_mads(mocker, MadsSteeringModeOnBrake.REMAIN_ACTIVE)
    self.mads.main_enabled_toggle = True
    self.mads.allow_always = True  # every Hyundai CAN-FD car gets this, so the LFA button works with cruise main off
    self.mads.keep_lateral_on_main_off = True  # set from the platform flag on the LX3

  def _main_on(self):
    self.sd.CS_prev = cruise_available(False)
    self.mads.update(cruise_available(True), car_state_sp(False))

  def _main_off(self):
    self.mads.enabled = True
    self.sd.CS_prev = cruise_available(True)
    self.mads.update(cruise_available(False), car_state_sp(False))

  def test_cruise_main_still_engages_lateral(self):
    self._main_on()
    assert self.sd.events_sp.has(EventNameSP.lkasEnable)

  def test_cruise_main_off_leaves_lateral_engaged(self):
    self._main_off()
    assert not self.sd.events_sp.has(EventNameSP.lkasDisable)

  def test_cruise_main_engage_follows_the_general_setting(self):
    # nothing special on the engage side: the cruise-main button brings lateral up exactly as on any other
    # stock-supported car, so the general MadsMainCruiseAllowed setting still decides
    self.mads.main_enabled_toggle = False
    self._main_on()
    assert not self.sd.events_sp.has(EventNameSP.lkasEnable)

  def test_main_off_still_disables_lateral_on_other_cars(self):
    self.mads.keep_lateral_on_main_off = False
    self._main_off()
    assert self.sd.events_sp.has(EventNameSP.lkasDisable)

  def test_lkas_button_switches_lateral_off_on_its_own(self):
    self.mads.enabled = True
    self.sd.enabled = False
    self.sd.CS_prev = cruise_available(True)
    self.mads.update(press_lkas(cruise_available(True)), car_state_sp(False))
    assert self.sd.events_sp.has(EventNameSP.lkasDisable)
    assert not self.sd.events_sp.has(EventNameSP.manualLongitudinalRequired)

  def test_lkas_button_still_engages_with_cruise_main_off(self):
    self.mads.enabled = False
    self.sd.enabled = False
    self.sd.CS_prev = cruise_available(False)
    self.mads.update(press_lkas(cruise_available(False)), car_state_sp(False))
    assert self.sd.events_sp.has(EventNameSP.lkasEnable)
