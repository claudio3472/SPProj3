import tenseal as ts, numpy as np, sys, pickle


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def vector_from_scheme(context, scheme, vector):
    if scheme == "ckks":
        return ts.ckks_vector(context, vector)
    elif scheme == "bfv":
        return ts.bfv_vector(context, vector)
    else:
        raise ValueError("scheme doesn't exist")
    
def getQuartile(context, scheme, evector, size, index):
    mask = np.zeros(size)

    if round(index) == index:
        mask[int(index)] = 1
    else:
        mask[int(np.floor(index))] = 0.5
        mask[int(np.ceil(index))] = 0.5
        
    return evector.dot(vector_from_scheme(context, scheme, mask))

def getQuartiles(context, scheme, evector, size):
    quartile_2_index = (size - 1) / 2
    quartile_1_index = (quartile_2_index - 1) / 2
    quartile_3_index = size - quartile_1_index - 1
    
    return (
        getQuartile(context, scheme, evector, size, quartile_1_index),
        getQuartile(context, scheme, evector, size, quartile_2_index),
        getQuartile(context, scheme, evector, size, quartile_3_index),
    )

def main(argv):
    if len(argv) < 3:
        eprint(f"Usage: {argv[0]} <encrypted_data> <encrypted_results>")
        return 1

    with open(argv[1], 'rb') as f:
        encrypted_data = pickle.load(f)

    scheme = encrypted_data['scheme']
    context = ts.context_from(encrypted_data['context'])

    if scheme == 'ckks':
        evector = ts.ckks_vector_from(context, encrypted_data['data'])
    elif scheme == 'bfv':
        evector = ts.bfv_vector_from(context, encrypted_data['data'])
    else:
        eprint('invalid scheme in file')
        return 2

    mean = evector.sum() * (1 / evector.size())
    quartile_1, quartile_2, quartile_3 = getQuartiles(context, scheme, evector, evector.size())

    encrypted_results = {
        'mean': mean.serialize(),
        'quartile 1': quartile_1.serialize(),
        'quartile 2': quartile_2.serialize(),
        'quartile 3': quartile_3.serialize(),
    }

    with open(argv[2], 'wb') as f:
        pickle.dump(encrypted_results, f)
    
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
