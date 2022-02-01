def gen_html(plotlychart):
    return """
  <html>
    <head>
      <meta charset="utf-8">
      <title>Leaderboard</title>
      <style>
        body {
          background-color: rgb(14, 17, 23);               
        }
      </style>""" + "<body>" + plotlychart + "</body></html>"
