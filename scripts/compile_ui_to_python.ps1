cd .\src\ui_elements\

$files = @(
  "available", "bonusingredient", "bottlewindow",
  "cocktailmanager", "calibration", "customdialog",
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
  pyuic5 -x .\$f.ui -o .\$f.py
}

cd ..\..