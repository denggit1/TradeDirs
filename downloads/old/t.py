def test2500():
    import pymysql
    sn = [['1and1000_bian_api', 'freq25', 'BCHUSDT', '608.98', '6'], ['1and1000_bian_api', 'freq25', 'LTCUSDT', '171.34', '6'], ['1and1000_bian_api', 'freq25', 'LINKUSDT', '23.206', '6'], ['1and1000_bian_api', 'freq25', 'ADAUSDT', '1.52790', '6'], ['1and1000_bian_api', 'freq25', 'BNBUSDT', '364.490', '6'], ['1and1000_bian_api', 'freq25', 'TRXUSDT', '0.07285', '6'], ['1and1000_bian_api', 'freq25', 'EOSUSDT', '5.316', '6'], ['1and1000_bian_api', 'freq25', 'XRPUSDT', '0.8797', '6'], ['1and1000_bian_api', 'freq25', 'ETCUSDT', '59.525', '6'], ['1and1000_bian_api', 'freq25', 'DOGEUSDT', '0.323520', '6'], ['1and1000_bian_api', 'freq25', 'DOTUSDT', '22.625', '6'], ['1and1000_bian_api', 'freq25', 'MATICUSDT', '1.36440', '6'], ['1and1000_bian_api', 'freq25', 'FILUSDT', '73.536', '6'], ['1and1000_bian_api', 'freq25', '1000SHIBUSDT', '0.006796', '6'], ['1and1000_bian_api', 'freq25', 'ICPUSDT', '66.43', '6'], ['1and1000_bian_api', 'freq25', 'SUSHIUSDT', '9.4140', '6'], ['1and1000_bian_api', 'freq25', 'VETUSDT', '0.113060', '6'], ['1and1000_bian_api', 'freq25', 'THETAUSDT', '8.4900', '6'], ['1and1000_bian_api', 'freq25', 'OMGUSDT', '5.1721', '6'], ['1and1000_bian_api', 'freq25', 'XLMUSDT', '0.33958', '6'], ['1and1000_bian_api', 'freq25', 'ZECUSDT', '134.34', '6'], ['1and1000_bian_api', 'freq25', 'DASHUSDT', '173.60', '6'], ['1and1000_bian_api', 'freq25', 'UNIUSDT', '23.1870', '6'], ['1and1000_bian_api', 'freq25', 'XMRUSDT', '256.25', '6'], ['1and1000_bian_api', 'freq25', 'CHZUSDT', '0.34089', '6']]
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd="Mysql_123", db='freq')
    cur = conn.cursor()
    sql = 'insert into freq_param (api_name, trade_name, trade_code, ticker_dfp, trade_num_usd) values ' \
          '(%s, %s, %s, %s, %s);'
    for s in sn:
        cur.execute(sql, ["1and{}_bian_api".format("2500"), s[1], s[2], s[3], s[4]])
        conn.commit()
    # list
    coin_list = ['COMP', 'BAT', 'ATOM', 'WAVES', 'NEO']
    for coin in coin_list:
        cur.execute(sql, ["1and{}_bian_api".format("2500"), 'freq25', coin+"USDT", 0, 0])
        conn.commit()
    conn.close()

def test5000():
    import pymysql
    sn = [['1and1000_bian_api', 'freq25', 'BCHUSDT', '608.98', '6'], ['1and1000_bian_api', 'freq25', 'LTCUSDT', '171.34', '6'], ['1and1000_bian_api', 'freq25', 'LINKUSDT', '23.206', '6'], ['1and1000_bian_api', 'freq25', 'ADAUSDT', '1.52790', '6'], ['1and1000_bian_api', 'freq25', 'BNBUSDT', '364.490', '6'], ['1and1000_bian_api', 'freq25', 'TRXUSDT', '0.07285', '6'], ['1and1000_bian_api', 'freq25', 'EOSUSDT', '5.316', '6'], ['1and1000_bian_api', 'freq25', 'XRPUSDT', '0.8797', '6'], ['1and1000_bian_api', 'freq25', 'ETCUSDT', '59.525', '6'], ['1and1000_bian_api', 'freq25', 'DOGEUSDT', '0.323520', '6'], ['1and1000_bian_api', 'freq25', 'DOTUSDT', '22.625', '6'], ['1and1000_bian_api', 'freq25', 'MATICUSDT', '1.36440', '6'], ['1and1000_bian_api', 'freq25', 'FILUSDT', '73.536', '6'], ['1and1000_bian_api', 'freq25', '1000SHIBUSDT', '0.006796', '6'], ['1and1000_bian_api', 'freq25', 'ICPUSDT', '66.43', '6'], ['1and1000_bian_api', 'freq25', 'SUSHIUSDT', '9.4140', '6'], ['1and1000_bian_api', 'freq25', 'VETUSDT', '0.113060', '6'], ['1and1000_bian_api', 'freq25', 'THETAUSDT', '8.4900', '6'], ['1and1000_bian_api', 'freq25', 'OMGUSDT', '5.1721', '6'], ['1and1000_bian_api', 'freq25', 'XLMUSDT', '0.33958', '6'], ['1and1000_bian_api', 'freq25', 'ZECUSDT', '134.34', '6'], ['1and1000_bian_api', 'freq25', 'DASHUSDT', '173.60', '6'], ['1and1000_bian_api', 'freq25', 'UNIUSDT', '23.1870', '6'], ['1and1000_bian_api', 'freq25', 'XMRUSDT', '256.25', '6'], ['1and1000_bian_api', 'freq25', 'CHZUSDT', '0.34089', '6']]
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd="Mysql_123", db='freq')
    cur = conn.cursor()
    sql = 'insert into freq_param (api_name, trade_name, trade_code, ticker_dfp, trade_num_usd) values ' \
          '(%s, %s, %s, %s, %s);'
    for s in sn:
        cur.execute(sql, ["1and{}_bian_api".format("5000"), s[1], s[2], s[3], s[4]])
        conn.commit()
    # list
    coin_list = ['COMP', 'BAT', 'ATOM', 'WAVES', 'SOL', 'NEO', 'AVAX', 'ONT', 'LUNA', 'AAVE', 'MKR', 'QTUM', 'ALGO', 'ETH', 'CRV']
    for coin in coin_list:
        cur.execute(sql, ["1and{}_bian_api".format("5000"), 'freq25', coin+"USDT", 0, 0])
        conn.commit()
    conn.close()


def test10000():
    import pymysql
    sn = [['1and1000_bian_api', 'freq25', 'BCHUSDT', '608.98', '6'], ['1and1000_bian_api', 'freq25', 'LTCUSDT', '171.34', '6'], ['1and1000_bian_api', 'freq25', 'LINKUSDT', '23.206', '6'], ['1and1000_bian_api', 'freq25', 'ADAUSDT', '1.52790', '6'], ['1and1000_bian_api', 'freq25', 'BNBUSDT', '364.490', '6'], ['1and1000_bian_api', 'freq25', 'TRXUSDT', '0.07285', '6'], ['1and1000_bian_api', 'freq25', 'EOSUSDT', '5.316', '6'], ['1and1000_bian_api', 'freq25', 'XRPUSDT', '0.8797', '6'], ['1and1000_bian_api', 'freq25', 'ETCUSDT', '59.525', '6'], ['1and1000_bian_api', 'freq25', 'DOGEUSDT', '0.323520', '6'], ['1and1000_bian_api', 'freq25', 'DOTUSDT', '22.625', '6'], ['1and1000_bian_api', 'freq25', 'MATICUSDT', '1.36440', '6'], ['1and1000_bian_api', 'freq25', 'FILUSDT', '73.536', '6'], ['1and1000_bian_api', 'freq25', '1000SHIBUSDT', '0.006796', '6'], ['1and1000_bian_api', 'freq25', 'ICPUSDT', '66.43', '6'], ['1and1000_bian_api', 'freq25', 'SUSHIUSDT', '9.4140', '6'], ['1and1000_bian_api', 'freq25', 'VETUSDT', '0.113060', '6'], ['1and1000_bian_api', 'freq25', 'THETAUSDT', '8.4900', '6'], ['1and1000_bian_api', 'freq25', 'OMGUSDT', '5.1721', '6'], ['1and1000_bian_api', 'freq25', 'XLMUSDT', '0.33958', '6'], ['1and1000_bian_api', 'freq25', 'ZECUSDT', '134.34', '6'], ['1and1000_bian_api', 'freq25', 'DASHUSDT', '173.60', '6'], ['1and1000_bian_api', 'freq25', 'UNIUSDT', '23.1870', '6'], ['1and1000_bian_api', 'freq25', 'XMRUSDT', '256.25', '6'], ['1and1000_bian_api', 'freq25', 'CHZUSDT', '0.34089', '6']]
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd="Mysql_123", db='freq')
    cur = conn.cursor()
    sql = 'insert into freq_param (api_name, trade_name, trade_code, ticker_dfp, trade_num_usd) values ' \
          '(%s, %s, %s, %s, %s);'
    for s in sn:
        cur.execute(sql, ["1and{}_bian_api".format("10000"), s[1], s[2], s[3], s[4]])
        conn.commit()
    # list
    coin_list = ['COMP', 'BAT', 'ATOM', 'WAVES', 'SOL', 'NEO', 'AVAX', 'ONT', 'LUNA', 'AAVE', 'MKR', 'QTUM', 'ALGO', 'ETH', 'CRV']
    for coin in coin_list:
        cur.execute(sql, ["1and{}_bian_api".format("10000"), 'freq25', coin+"USDT", 0, 0])
        conn.commit()
    conn.close()

test2500()
test5000()
test10000()

