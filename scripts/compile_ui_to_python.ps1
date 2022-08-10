$files = @("available", "bonusingredient", "bottlewindow", "Cocktailmanager_2", "customdialog", "handadds", "Keyboard", "optionwindow", "passwordbuttons2", "progressbarwindow", "teamselection")

foreach ($f in $files) {
  pyuic5 -x .\$f.ui -o .\$f.py
}
