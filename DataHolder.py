import tenseal as ts, numpy as np, sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def getQuartile(context, evector, size, index):
    mask = np.zeros(size)

    if round(index) == index:
        mask[int(index)] = 1
        mask = ts.ckks_vector(context, mask)
        return evector.dot(mask)
    else:
        mask[int(np.floor(index))] = 1
        mask[int(np.ceil(index))] = 1
        mask = ts.ckks_vector(context, mask)
        return evector.dot(mask) * 0.5

def getQuartiles(context, evector, size):
    quartile_2_index = (size - 1) / 2
    quartile_1_index = (quartile_2_index - 1) / 2
    quartile_3_index = size - quartile_1_index - 1
    
    return (
        getQuartile(context, evector, size, quartile_1_index),
        getQuartile(context, evector, size, quartile_2_index),
        getQuartile(context, evector, size, quartile_3_index),
    )


poly_modulus = 8192

context = ts.context(ts.SCHEME_TYPE.CKKS, poly_modulus, coeff_mod_bit_sizes=[60, 40, 40, 60])
context.global_scale = pow(2, 40)
context.generate_galois_keys()

if len(sys.argv) < 2:
    eprint(f"Usage: {sys.argv[0]} <file>")
    sys.exit(1)

vector = np.loadtxt(sys.argv[1])
evector = ts.ckks_vector(context, vector)

mean = evector.sum() * (1 / evector.size())

quartile_1, quartile_2, quartile_3 = getQuartiles(context, evector, evector.size())

print("Mean:", mean.decrypt())
print("Qua1:", quartile_1.decrypt())
print("Qua2:", quartile_2.decrypt())
print("Qua3:", quartile_3.decrypt())
