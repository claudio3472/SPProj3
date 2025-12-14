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

def vector_from_scheme_2(context, scheme, vector):
    if scheme == "ckks":
        return ts.ckks_vector_from(context, vector)
    elif scheme == "bfv":
        return ts.bfv_vector_from(context, vector)
    else:
        raise ValueError("scheme doesn't exist")
    
def getQuartile(context, scheme, evector, size, index):
    mask = np.zeros(size)

    if round(index) == index:
        mask[int(index)] = 1
    else:
        mask[int(np.floor(index))] = 1
        mask[int(np.ceil(index))] = 1
        
    return evector.dot(mask)

def getQuartiles(context, scheme, evector, size):
    quartile_2_index = (size - 1) / 2
    quartile_1_index = (quartile_2_index - 1) / 2
    quartile_3_index = size - quartile_1_index - 1
    
    return (
        getQuartile(context, scheme, evector, size, quartile_1_index),
        getQuartile(context, scheme, evector, size, quartile_2_index),
        getQuartile(context, scheme, evector, size, quartile_3_index),
    )

def encrypt(scheme, data_path, server_file_path, encrypted_data_path):
    vector = np.loadtxt(data_path)
    #vector = [3, 4, 1]
    
    #print(vector.size)
    #poly_modulus = 2 ** 13
    poly_modulus = 2 ** max(13, (int(np.ceil(np.log2(vector.size)) + 1)))
    #print(poly_modulus)

    if scheme == 'ckks':
        context = ts.context(ts.SCHEME_TYPE.CKKS, poly_modulus, coeff_mod_bit_sizes=[60, 40, 40, 60])
    elif scheme == 'bfv':
        #poly_modulus = 2**12 # fuck bfv
        print("\n", poly_modulus, sep="")
        context = ts.context(ts.SCHEME_TYPE.BFV, poly_modulus_degree=poly_modulus, plain_modulus=2013265921, coeff_mod_bit_sizes=[60, 40, 40, 60])
    else:
        eprint("invalid scheme value")
        eprint("only ckks and bfv available")
        return 2
    
    context.global_scale = 2 ** 40
    context.generate_galois_keys()
    
    evector = vector_from_scheme(context, scheme, vector)

    #power = evector * evector

    #print(power.decrypt())
    #return

    server_file = {
        'scheme': scheme,
        'size': evector.size(),
        'context': context.serialize(save_secret_key=True),
    }

    public_context = context.copy()
    public_context.make_context_public()
    
    encrypted_data = {
        'scheme': scheme,
        'context': public_context.serialize(),
        'data': evector.serialize(),
    }

    with open(server_file_path, 'wb') as f:
        pickle.dump(server_file, f)

    with open(encrypted_data_path, 'wb') as f:
        pickle.dump(encrypted_data, f)
    
    # power = evector ** 2
    # print(power.decrypt())
    
    # mean = evector.sum()
    # quartile_1, quartile_2, quartile_3 = getQuartiles(context, scheme, evector, evector.size())

    # print("Mean:", mean.decrypt())
    # print("Qua1:", quartile_1.decrypt())
    # print("Qua2:", quartile_2.decrypt())
    # print("Qua3:", quartile_3.decrypt())

    return
    
def decrypt(server_file_path, encrypted_results_path):
    with open(server_file_path, 'rb') as f:
        server_file = pickle.load(f)

    with open(encrypted_results_path, 'rb') as f:
        encrypted_results = pickle.load(f)

    scheme = server_file['scheme']
    context = ts.context_from(server_file['context'])
    size = server_file['size']

    mean = round(vector_from_scheme_2(context, scheme, encrypted_results['mean']).decrypt()[0] / size, 4)
    quartile_1 = round(vector_from_scheme_2(context, scheme, encrypted_results['quartile 1'][0]).decrypt()[0] / encrypted_results['quartile 1'][1], 4)
    quartile_2 = round(vector_from_scheme_2(context, scheme, encrypted_results['quartile 2'][0]).decrypt()[0] / encrypted_results['quartile 2'][1], 4)
    quartile_3 = round(vector_from_scheme_2(context, scheme, encrypted_results['quartile 3'][0]).decrypt()[0] / encrypted_results['quartile 3'][1], 4)
    alz = np.round(np.array(vector_from_scheme_2(context, scheme, encrypted_results['alz']).decrypt())) / 1000
    
    print("mean:", mean)
    print("quartile 1:", quartile_1)
    print("quartile 2:", quartile_2)
    print("quartile 3:", quartile_3)
    print("alz:", alz)
    
    return

def main(argv):
    if len(argv) < 4:
        eprint(f"Usage:\n\t{argv[0]} <encrypt> <scheme> <data> <server_file> <encrypted_data>\n\t{argv[0]} <decrypt> <server_file> <encrypted_results>")
        return 1

    if argv[1].lower() in ["e", "encrypt"]:
        if len(argv) < 6:
            eprint("invalid encrypt command")
            eprint(f"Usage:\n\t{argv[0]} <encrypt> <scheme> <data> <server_file> <encrypted_data>\n\t{argv[0]} <decrypt> <server_file> <encrypted_results>")
            return 1
        
        encrypt(argv[2].lower(), argv[3], argv[4], argv[5])
    elif argv[1].lower() in ["d", "decrypt"]:
        decrypt(argv[2], argv[3])
        
    return 0

    
if __name__ == "__main__":
    sys.exit(main(sys.argv))
