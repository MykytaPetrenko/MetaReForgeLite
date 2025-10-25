def dot(a: list, b: list):
    return sum([a[i]*b[i] for i in range(len(a))])


def transpose(mat: list):
    return [[mat[j][i] for j in range(len(mat))] for i in range(len(mat[0]))]
