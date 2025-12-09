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

def encrypt(scheme, data_path, server_file_path, encrypted_data_path):
    vector = np.loadtxt(data_path)

     # Maybe should be changed so it doenst complain but it increases time it takes to do stuff
    poly_modulus = 8192

    if scheme == 'ckks':
        context = ts.context(ts.SCHEME_TYPE.CKKS, poly_modulus, coeff_mod_bit_sizes=[60, 40, 40, 60])
    elif scheme == 'bfv':
        context = ts.context(ts.SCHEME_TYPE.BFV, poly_modulus_degree=4096, plain_modulus=1032193)
    else:
        eprint("invalid scheme value")
        eprint("only ckks and bfv available")
        return 2
    
    context.global_scale = pow(2, 40)
    context.generate_galois_keys()
    
    evector = vector_from_scheme(context, scheme, vector)
    
    server_file = {
        'scheme': scheme,
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
    
    
    mean = evector.sum() * (1 / evector.size())
    quartile_1, quartile_2, quartile_3 = getQuartiles(context, scheme, evector, evector.size())

    print("Mean:", mean.decrypt())
    print("Qua1:", quartile_1.decrypt())
    print("Qua2:", quartile_2.decrypt())
    print("Qua3:", quartile_3.decrypt())

    return
    
def decrypt(server_file_path, encrypted_results_path):
    with open(server_file_path, 'rb') as f:
        server_file = pickle.load(f)

    with open(encrypted_results_path, 'rb') as f:
        encrypted_results = pickle.load(f)

    scheme = server_file['scheme']
    context = ts.context_from(server_file['context'])
    
    if scheme == 'ckks':
        for label, evector in encrypted_results.items():
            result = round(ts.ckks_vector_from(context, evector).decrypt()[0], 4)
            print(f"{label}: {result}")
            
    elif scheme == 'bfv':
        for label, evector in encrypted_results.items():
            result = ts.bfv_vector_from(context, evector).decrypt()
            print(f"{label}: {result}")
            
    else:
        raise ValueError('invalid scheme in file')
    
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
