WIDTH = 800
BINS = 512

lut = []
for x in range(WIDTH):
    val = int((2 ** (9 * x / 799)) - 1)
    val = min(511, max(0, val))
    lut.append(val)

print("logic [8:0] lut [0:799] = '{")
for i in range(0, WIDTH, 8):
    row = lut[i:i+8]
    line = ", ".join(f"9'd{v:3d}" for v in row)
    comma = "," if i + 8 < WIDTH else ""
    print(f"    {line}{comma}")
print("};")