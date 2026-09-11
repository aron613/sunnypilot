"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from openpilot.selfdrive.ui.sunnypilot.layouts.settings.vehicle.brands.base import BrandSettings
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.sunnypilot.widgets.list_view import multiple_button_item_sp
from opendbc.car.hyundai.values import CAR, UNSUPPORTED_LONGITUDINAL_CAR


class HyundaiSettings(BrandSettings):
  def __init__(self):
    super().__init__()
    self.alpha_long_available = False

    tuning_texts = [tr("Off"), tr("Dynamic"), tr("Predictive")]
    self.longitudinal_tuning_item = multiple_button_item_sp(tr("Custom Longitudinal Tuning"), "", tuning_texts,
                                                            button_width=300, callback=self._on_tuning_selected,
                                                            param="HyundaiLongitudinalTuning", inline=False)
    hda_texts = [tr("Off"), tr("Exp A"), tr("Exp B"), tr("Exp C")]
    self.hda_experiment_item = multiple_button_item_sp(tr("LX3 HDA Suppression Experiment"), "", hda_texts,
                                                       button_width=200, callback=self._on_hda_experiment_selected,
                                                       param="HyundaiLx3HdaSuppressionExperiment", inline=False)
    self.items = [self.longitudinal_tuning_item, self.hda_experiment_item]

  @staticmethod
  def _on_tuning_selected(index):
    ui_state.params.put("HyundaiLongitudinalTuning", index)

  @staticmethod
  def _on_hda_experiment_selected(index):
    ui_state.params.put("HyundaiLx3HdaSuppressionExperiment", index)

  def update_settings(self):
    self.alpha_long_available = False
    bundle = ui_state.params.get("CarPlatformBundle")
    if bundle:
      platform = bundle.get("platform")
      self.alpha_long_available = CAR[platform] not in set().union(*UNSUPPORTED_LONGITUDINAL_CAR.values())
    elif ui_state.CP is not None:
      self.alpha_long_available = ui_state.CP.alphaLongitudinalAvailable

    tuning_param = int(ui_state.params.get("HyundaiLongitudinalTuning") or "0")
    long_enabled = ui_state.has_longitudinal_control

    long_tuning_descs = [
      tr("Your vehicle will use the Default longitudinal tuning."),
      tr("Your vehicle will use the Dynamic longitudinal tuning."),
      tr("Your vehicle will use the Predictive longitudinal tuning."),
    ]
    long_tuning_desc = long_tuning_descs[tuning_param] if tuning_param < len(long_tuning_descs) else long_tuning_descs[0]

    longitudinal_tuning_disabled = not ui_state.is_offroad() or not long_enabled
    if longitudinal_tuning_disabled:
      if not ui_state.is_offroad():
        long_tuning_desc = tr("This feature is unavailable while the car is onroad.")
      elif not long_enabled:
        long_tuning_desc = tr("This feature is unavailable because sunnypilot Longitudinal Control (Alpha) is not enabled.")

    self.longitudinal_tuning_item.action_item.set_enabled(not longitudinal_tuning_disabled)
    self.longitudinal_tuning_item.set_description(long_tuning_desc)
    self.longitudinal_tuning_item.show_description(True)
    self.longitudinal_tuning_item.action_item.set_selected_button(tuning_param)
    self.longitudinal_tuning_item.set_visible(self.alpha_long_available)

    # Palisade LX3 only: opt-in HDA suppression experiments (stock cruise + openpilot lateral), default Off
    is_lx3 = False
    if bundle:
      is_lx3 = bundle.get("platform") == CAR.HYUNDAI_PALISADE_LX3
    elif ui_state.CP is not None:
      is_lx3 = ui_state.CP.carFingerprint == CAR.HYUNDAI_PALISADE_LX3
    hda_param = int(ui_state.params.get("HyundaiLx3HdaSuppressionExperiment") or "0")
    hda_descs = [
      tr("Off: openpilot pauses steering while stock cruise is engaged (safe default)."),
      tr("Exp A: openpilot keeps steering with cruise on and reports LFA inactive to the ADAS ECU. Watchdog drops lateral on takeover."),
      tr("Exp B: openpilot keeps steering with cruise on and blanks two more lane-line bytes in the spoof. Watchdog drops lateral on takeover."),
      tr("Exp C: A and B together. Watchdog drops lateral on takeover."),
    ]
    hda_desc = hda_descs[hda_param] if hda_param < len(hda_descs) else hda_descs[0]
    if not ui_state.is_offroad():
      hda_desc = tr("This feature is unavailable while the car is onroad.")
    self.hda_experiment_item.action_item.set_enabled(ui_state.is_offroad())
    self.hda_experiment_item.set_description(hda_desc)
    self.hda_experiment_item.show_description(True)
    self.hda_experiment_item.action_item.set_selected_button(hda_param)
    self.hda_experiment_item.set_visible(is_lx3)
