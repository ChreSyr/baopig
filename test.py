import docs as bp

app = bp.Application(size=(600, 400))
exit(app.launch())
sc = bp.Scene(app)
t = bp.Timer(5)
b = bp.Button(sc, "Hello World", sticky="center", command=t.start)
bp.DynamicText(sc, t.get_time_left, pos=b.midbottom)
app.launch()
