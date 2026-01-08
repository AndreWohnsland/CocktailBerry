cd .\src\ui_elements\

$files = @(
  "available", "bonusingredient", "bottlewindow",
  "cocktailmanager", "calibration", "calibration_real", "calibration_target", "customdialog",
  "datepicker", "keyboard",
  "optionwindow", "numpad", "progressbarwindow",
  "teamselection", "passworddialog", "customprompt",
  "logwindow", "rfidwriter", "wifiwindow",
  "customcolor", "addonwindow", "addonmanager",
  "datawindow", "cocktail_selection",
  "picture_window", "refill_prompt",
  "config_window", "resource_window"
)

foreach ($f in $files) {
  pyuic6 -x .\$f.ui -o .\$f.py
}

cd ..\..