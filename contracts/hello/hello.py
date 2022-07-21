import asyncio
import sys
import json

sys.path.append('./')

from console import blue_strong, blue, red
from utils import deploy_account, print_n_wait, get_evaluator, fund_account, get_client, get_account_client
from starkware.starknet.public.abi import get_selector_from_name

with open("./hints.json", "r") as f:
  data = json.load(f)

async def main():
    blue_strong.print("Your mission:")
    blue.print("\t 1) deploy an account contract with an '__execute__' entrypoint")
    blue.print("\t 2) fetch the 'random' storage_variable from the validator contract")
    blue.print("\t 3) pass 'random' via calldata to your account contract\n")

    #
    # Initialize StarkNet Client
    #
    client = get_client()
    acc_client, addr = get_account_client()

    #
    # Compile and Deploy `hello.cairo`
    #
    hello, hello_addr = await deploy_account(client=acc_client, contract_path=data['HELLO'])

    #
    # Transfer ETH to pay for fees
    #
    reward_account = await fund_account(hello_addr)
    if reward_account == "":
      red.print("Account must have ETH to cover transaction fees")
      return

    #
    # Check answer against 'evaluator.cairo'
    #    
    evaluator, evaluator_address = await get_evaluator(client)
    (random, ) = await evaluator.functions["get_random"].call()

    prepared = hello.functions["__execute__"].prepare(
        contract_address=evaluator_address,
        selector=get_selector_from_name("validate_hello"),
        calldata_len=2,
        calldata=[random, reward_account])
    invocation = await prepared.invoke(max_fee=data['MAX_FEE'])

    await print_n_wait(acc_client, invocation)

asyncio.run(main())
