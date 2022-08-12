cd .\src\ui_elements\

$files = @("available", "bonusingredient", "bottlewindow", "cocktailmanager", "calibration", "customdialog", "handadds", "keyboard", "optionwindow", "passwordbuttons", "progressbarwindow", "teamselection")

foreach ($f in $files) {
  pyuic5 -x .\$f.ui -o .\$f.py
}
