import json
import time
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from solcx import compile_source, install_solc
from web3 import Web3

alchemy_url = "https://eth-sepolia.g.alchemy.com/v2/{your_end_point}"
CMC_API = "{your_cmc_api_key}"
my_account = "{your_wallet_address}"
private_key = "{your_wallet_private_key}"

MyOracleSource = "./contracts/MyOracle.sol"

def get_eth_price():
    print("Fetching latest ETH price....")
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    parameters = {
        'symbol': 'ETH',
        'convert': 'USD'
    }
    headers = {
        'X-CMC_PRO_API_KEY': CMC_API
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        eth_in_usd = data['data']['ETH']['quote']['USD']['price']
        return eth_in_usd
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)

def compile_contract(w3):
    with open(MyOracleSource, 'r') as file:
        oracle_code = file.read()

    compiled_sol = compile_source(
        oracle_code,
        output_values=['abi', 'bin']
    )

    contract_id, contract_interface = compiled_sol.popitem()

    bytecode = contract_interface['bin']
    abi = contract_interface['abi']

    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    print("Compile completed!")
    return Contract

def deploy_oracle(w3, contract):
    deploy_txn = contract.constructor().build_transaction({
        'from': my_account,
        'nonce': w3.eth.get_transaction_count(my_account),
        'gas': 400000,
        'gasPrice': w3.to_wei('20', 'gwei') 
    })

    signed_txn = w3.eth.account.sign_transaction(deploy_txn, private_key=private_key)
    print("Deploying Contract...")
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    txn_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    oracle_address = txn_receipt.contractAddress
    return oracle_address

def update_oracle(w3, contract, eth_price):
    set_txn = contract.functions.setEtherPrice(eth_price).build_transaction({
        'from': my_account,
        'to': contract.address,
        'nonce': w3.eth.get_transaction_count(my_account),
        'gas': 200000,
        'gasPrice': w3.to_wei('20', 'gwei') 
    })

    signed_txn = w3.eth.account.sign_transaction(set_txn, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    txn_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return txn_receipt

def main():
    install_solc('0.8.17')
    w3 = Web3(Web3.HTTPProvider(alchemy_url))
    w3.eth.default_account = my_account

    if not w3.is_connected():
        print('Not connected to Alchemy endpoint')
        exit(-1)

    MyOracle = compile_contract(w3)
    MyOracle.address = deploy_oracle(w3, MyOracle)
    print("oracle address:", MyOracle.address)

    event_filter = MyOracle.events.PriceUpdated.create_filter(fromBlock='latest')

    print("Connected to Alchemy endpoint")
    while True:
        print("Waiting for an oracle update request...")
        for event in event_filter.get_new_entries():
            if event.event == "PriceUpdated":
                print("------------------------------------------")
                print("Callback found:")
                ETH_price = get_eth_price()
                print(f"Pulled Current ETH price: {ETH_price}")
                print("Writing to blockchain...")
                txn = update_oracle(w3, MyOracle, int(ETH_price))
                print("Transaction complete!")
                print(f"blockNumber: {txn.blockNumber} gasUsed: {txn.gasUsed}")
                print("------------------------------------------")
            else:
                print("Something went wrong...please try again")
        time.sleep(5)


if __name__ == "__main__":
    main()