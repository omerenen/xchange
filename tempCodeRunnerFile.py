t0 = time.time()
        result_buy = mexc.buy(target_coin, 10.1)
        resp_buy = result_buy["bid_quantity"]
        sleep(10)
        result_sell = mexc.sell(target_coin, resp_buy)
        print("delta---->", time.time()-t0)
        print(result_buy)
        print(result_sell)