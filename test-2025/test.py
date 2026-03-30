import aspose.threed as a3d

scene = a3d.Scene.from_file('BMW850.3ds')
scene.save('couch.stl')

