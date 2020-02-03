import pickle

from addressparser import DBConnect
from elasticsearch import TransportError
from tqdm import tqdm


def load_pickle(filename='parsed.pickle'):
    # for reading also binary mode is important
    dbfile = open(filename, 'rb')
    parsed_list = pickle.load(dbfile)
    dbfile.close()
    return parsed_list


def rename_key(addr_list):
    '''
    renames key 'house number'>'house_number' and 'postal code'>'postal_code'
    '''
    results = []
    for each in addr_list:
        if 'house number' in each:
            each['house_number'] = each['house number']
            del each['house number']
        elif 'postal code' in each:
            each['postal_code'] = each['postal code']
            del each['postal code']
        results.append(each)
    return results


def load_data():
    receiver_parsed_addr_list = load_pickle(filename='db_data/address_list.pkl')
    receiver_name_list = load_pickle(filename='db_data/name_list.pkl')
    # rename_key function applies only to receiver_addr and receiver_name file
    #receiver_parsed_addr_list = rename_key(receiver_parsed_addr_list)

    return concat_name_addr(receiver_parsed_addr_list, receiver_name_list)


def concat_name_addr(addr_list, name_list):
    assert len(addr_list) == len(name_list)
    for i, each in enumerate(addr_list):
        each['name'] = name_list[i]
    return addr_list


def insert_to_es(datas):
    es = DBConnect()

    for i, data in tqdm(enumerate(datas)):
        try:
            res = es.index(index="address_name", doc_type='address', id=i, body=data)
        except TransportError as e:
            print(e)
            return False
    return True

def main():

    datas = load_data()

    insert_to_es(datas)

if __name__ == '__main__':
    main()



