import pywavefront
import meshio
import numpy as np

def convert_3ds_to_stl(input_file, output_file):
    # 使用pywavefront加载3ds文件
    mesh = pywavefront.Wavefront(input_file, collect_faces=True)

    # 提取顶点和面
    vertices = np.array(mesh.vertices)
    faces = np.array(mesh.faces)

    # 创建meshio Mesh对象
    meshio_mesh = meshio.Mesh(points=vertices, cells=[('triangle', faces)])

    # 将meshio Mesh对象保存为STL文件
    meshio.write(output_file, meshio_mesh)

# 调用函数进行转换
input_file = "BMW850.3ds"
output_file = "test.stl"
convert_3ds_to_stl(input_file, output_file)
