"""Symbol master: curated NSE large/mid-cap equities, ETFs and indices.

Yahoo Finance tickers: NSE symbols carry the `.NS` suffix, indices use `^` codes.
"""

INDICES = [
    {"symbol": "^NSEI", "name": "NIFTY 50", "type": "index"},
    {"symbol": "^BSESN", "name": "SENSEX", "type": "index"},
    {"symbol": "^NSEBANK", "name": "NIFTY BANK", "type": "index"},
    {"symbol": "^CNXIT", "name": "NIFTY IT", "type": "index"},
    {"symbol": "^INDIAVIX", "name": "INDIA VIX", "type": "index"},
]

EQUITIES = [
    # symbol (without .NS), name, sector
    ("RELIANCE", "Reliance Industries", "Energy"),
    ("TCS", "Tata Consultancy Services", "IT"),
    ("HDFCBANK", "HDFC Bank", "Banking"),
    ("ICICIBANK", "ICICI Bank", "Banking"),
    ("INFY", "Infosys", "IT"),
    ("BHARTIARTL", "Bharti Airtel", "Telecom"),
    ("SBIN", "State Bank of India", "Banking"),
    ("LICI", "Life Insurance Corporation", "Insurance"),
    ("ITC", "ITC", "FMCG"),
    ("HINDUNILVR", "Hindustan Unilever", "FMCG"),
    ("LT", "Larsen & Toubro", "Infrastructure"),
    ("KOTAKBANK", "Kotak Mahindra Bank", "Banking"),
    ("AXISBANK", "Axis Bank", "Banking"),
    ("MARUTI", "Maruti Suzuki", "Auto"),
    ("SUNPHARMA", "Sun Pharmaceutical", "Pharma"),
    ("TITAN", "Titan Company", "Consumer"),
    ("ULTRACEMCO", "UltraTech Cement", "Cement"),
    ("ASIANPAINT", "Asian Paints", "Consumer"),
    ("NTPC", "NTPC", "Power"),
    ("ONGC", "Oil & Natural Gas Corporation", "Energy"),
    ("BAJFINANCE", "Bajaj Finance", "NBFC"),
    ("HCLTECH", "HCL Technologies", "IT"),
    ("ADANIENT", "Adani Enterprises", "Conglomerate"),
    ("ADANIPORTS", "Adani Ports & SEZ", "Infrastructure"),
    ("POWERGRID", "Power Grid Corporation", "Power"),
    ("TATAMOTORS", "Tata Motors", "Auto"),
    ("TATASTEEL", "Tata Steel", "Metals"),
    ("COALINDIA", "Coal India", "Mining"),
    ("BAJAJFINSV", "Bajaj Finserv", "NBFC"),
    ("WIPRO", "Wipro", "IT"),
    ("M&M", "Mahindra & Mahindra", "Auto"),
    ("NESTLEIND", "Nestle India", "FMCG"),
    ("JSWSTEEL", "JSW Steel", "Metals"),
    ("HDFCLIFE", "HDFC Life Insurance", "Insurance"),
    ("SBILIFE", "SBI Life Insurance", "Insurance"),
    ("TECHM", "Tech Mahindra", "IT"),
    ("GRASIM", "Grasim Industries", "Cement"),
    ("HINDALCO", "Hindalco Industries", "Metals"),
    ("DRREDDY", "Dr. Reddy's Laboratories", "Pharma"),
    ("CIPLA", "Cipla", "Pharma"),
    ("DIVISLAB", "Divi's Laboratories", "Pharma"),
    ("APOLLOHOSP", "Apollo Hospitals", "Healthcare"),
    ("BRITANNIA", "Britannia Industries", "FMCG"),
    ("EICHERMOT", "Eicher Motors", "Auto"),
    ("HEROMOTOCO", "Hero MotoCorp", "Auto"),
    ("BAJAJ-AUTO", "Bajaj Auto", "Auto"),
    ("TATACONSUM", "Tata Consumer Products", "FMCG"),
    ("BPCL", "Bharat Petroleum", "Energy"),
    ("SHRIRAMFIN", "Shriram Finance", "NBFC"),
    ("INDUSINDBK", "IndusInd Bank", "Banking"),
    ("VEDL", "Vedanta", "Metals"),
    ("DLF", "DLF", "Realty"),
    ("HAL", "Hindustan Aeronautics", "Defence"),
    ("BEL", "Bharat Electronics", "Defence"),
    ("SIEMENS", "Siemens", "Capital Goods"),
    ("ABB", "ABB India", "Capital Goods"),
    ("TRENT", "Trent", "Retail"),
    ("ZOMATO", "Zomato (Eternal)", "Internet"),
    ("PAYTM", "One97 Communications (Paytm)", "Fintech"),
    ("NYKAA", "FSN E-Commerce (Nykaa)", "Internet"),
    ("POLICYBZR", "PB Fintech (PolicyBazaar)", "Fintech"),
    ("IRCTC", "IRCTC", "Travel"),
    ("INDIGO", "InterGlobe Aviation (IndiGo)", "Aviation"),
    ("PIDILITIND", "Pidilite Industries", "Chemicals"),
    ("SRF", "SRF", "Chemicals"),
    ("HAVELLS", "Havells India", "Consumer Durables"),
    ("DABUR", "Dabur India", "FMCG"),
    ("GODREJCP", "Godrej Consumer Products", "FMCG"),
    ("MARICO", "Marico", "FMCG"),
    ("COLPAL", "Colgate-Palmolive India", "FMCG"),
    ("AMBUJACEM", "Ambuja Cements", "Cement"),
    ("SHREECEM", "Shree Cement", "Cement"),
    ("BANKBARODA", "Bank of Baroda", "Banking"),
    ("PNB", "Punjab National Bank", "Banking"),
    ("CANBK", "Canara Bank", "Banking"),
    ("IDFCFIRSTB", "IDFC First Bank", "Banking"),
    ("FEDERALBNK", "Federal Bank", "Banking"),
    ("AUBANK", "AU Small Finance Bank", "Banking"),
    ("CHOLAFIN", "Cholamandalam Investment", "NBFC"),
    ("MUTHOOTFIN", "Muthoot Finance", "NBFC"),
    ("LICHSGFIN", "LIC Housing Finance", "NBFC"),
    ("RECLTD", "REC", "PSU Finance"),
    ("PFC", "Power Finance Corporation", "PSU Finance"),
    ("IRFC", "Indian Railway Finance Corp", "PSU Finance"),
    ("GAIL", "GAIL India", "Energy"),
    ("IOC", "Indian Oil Corporation", "Energy"),
    ("HINDPETRO", "Hindustan Petroleum", "Energy"),
    ("ADANIGREEN", "Adani Green Energy", "Renewables"),
    ("ADANIPOWER", "Adani Power", "Power"),
    ("TATAPOWER", "Tata Power", "Power"),
    ("JINDALSTEL", "Jindal Steel & Power", "Metals"),
    ("SAIL", "Steel Authority of India", "Metals"),
    ("NMDC", "NMDC", "Mining"),
    ("LUPIN", "Lupin", "Pharma"),
    ("AUROPHARMA", "Aurobindo Pharma", "Pharma"),
    ("ALKEM", "Alkem Laboratories", "Pharma"),
    ("TORNTPHARM", "Torrent Pharmaceuticals", "Pharma"),
    ("MAXHEALTH", "Max Healthcare", "Healthcare"),
    ("FORTIS", "Fortis Healthcare", "Healthcare"),
    ("LTIM", "LTIMindtree", "IT"),
    ("PERSISTENT", "Persistent Systems", "IT"),
    ("COFORGE", "Coforge", "IT"),
    ("MPHASIS", "Mphasis", "IT"),
    ("TATAELXSI", "Tata Elxsi", "IT"),
    ("KPITTECH", "KPIT Technologies", "IT"),
    ("TVSMOTOR", "TVS Motor Company", "Auto"),
    ("ASHOKLEY", "Ashok Leyland", "Auto"),
    ("BHARATFORG", "Bharat Forge", "Auto Ancillary"),
    ("MOTHERSON", "Samvardhana Motherson", "Auto Ancillary"),
    ("BOSCHLTD", "Bosch", "Auto Ancillary"),
    ("BALKRISIND", "Balkrishna Industries", "Auto Ancillary"),
    ("VBL", "Varun Beverages", "FMCG"),
    ("JUBLFOOD", "Jubilant FoodWorks", "QSR"),
    ("DMART", "Avenue Supermarts (DMart)", "Retail"),
    ("PAGEIND", "Page Industries", "Textiles"),
    ("BEML", "BEML", "Defence"),
    ("MAZDOCK", "Mazagon Dock Shipbuilders", "Defence"),
    ("COCHINSHIP", "Cochin Shipyard", "Defence"),
    ("RVNL", "Rail Vikas Nigam", "Infrastructure"),
    ("IRCON", "IRCON International", "Infrastructure"),
    ("NBCC", "NBCC India", "Infrastructure"),
    ("SUZLON", "Suzlon Energy", "Renewables"),
    ("IDEA", "Vodafone Idea", "Telecom"),
    ("YESBANK", "Yes Bank", "Banking"),
    ("JPL", "Jio Platforms", "Telecom"),
]

ETFS = [
    ("NIFTYBEES", "Nippon India Nifty 50 BeES", "Index ETF"),
    ("BANKBEES", "Nippon India Nifty Bank BeES", "Index ETF"),
    ("JUNIORBEES", "Nippon India Nifty Next 50 BeES", "Index ETF"),
    ("GOLDBEES", "Nippon India Gold BeES", "Gold ETF"),
    ("SILVERBEES", "Nippon India Silver BeES", "Silver ETF"),
    ("ITBEES", "Nippon India Nifty IT BeES", "Sector ETF"),
    ("PHARMABEES", "Nippon India Nifty Pharma BeES", "Sector ETF"),
    ("PSUBNKBEES", "Nippon India Nifty PSU Bank BeES", "Sector ETF"),
    ("CPSEETF", "CPSE ETF", "Thematic ETF"),
    ("MON100", "Motilal Oswal Nasdaq 100 ETF", "International ETF"),
    ("MAFANG", "Mirae Asset NYSE FANG+ ETF", "International ETF"),
    ("MOM100", "Motilal Oswal Nifty Midcap 100 ETF", "Index ETF"),
    ("HDFCSML250", "HDFC Nifty Smallcap 250 ETF", "Index ETF"),
    ("ICICINXT50", "ICICI Prudential Nifty Next 50 ETF", "Index ETF"),
    ("UTINIFTETF", "UTI Nifty 50 ETF", "Index ETF"),
    ("LIQUIDBEES", "Nippon India Liquid BeES", "Debt ETF"),
    ("MOM30IETF", "Motilal Oswal Nifty 200 Momentum 30 ETF", "Factor ETF"),
    ("LOWVOLIETF", "ICICI Prudential Nifty 100 Low Vol 30 ETF", "Factor ETF"),
    ("ALPHA", "Kotak Nifty Alpha 50 ETF", "Factor ETF"),
    ("AUTOBEES", "Nippon India Nifty Auto BeES", "Sector ETF"),
]


def _to_entry(sym: str, name: str, sector: str, type_: str) -> dict:
    return {
        "symbol": sym,
        "yahoo": f"{sym}.NS",
        "name": name,
        "sector": sector,
        "type": type_,
    }


ALL_SYMBOLS: list[dict] = (
    [_to_entry(s, n, sec, "equity") for s, n, sec in EQUITIES]
    + [_to_entry(s, n, sec, "etf") for s, n, sec in ETFS]
)

_BY_SYMBOL = {e["symbol"].upper(): e for e in ALL_SYMBOLS}


def lookup(symbol: str) -> dict | None:
    """Find a symbol entry. Accepts bare NSE code or Yahoo ticker."""
    key = symbol.upper().removesuffix(".NS").removesuffix(".BO")
    return _BY_SYMBOL.get(key)


def to_yahoo(symbol: str) -> str:
    """Map any user-supplied symbol to a Yahoo ticker (defaults to NSE)."""
    entry = lookup(symbol)
    if entry:
        return entry["yahoo"]
    s = symbol.upper()
    if s.startswith("^") or "." in s:
        return s
    return f"{s}.NS"


def search(query: str, limit: int = 15) -> list[dict]:
    q = query.strip().upper()
    if not q:
        return []
    starts, contains = [], []
    for e in ALL_SYMBOLS:
        sym, name = e["symbol"].upper(), e["name"].upper()
        if sym.startswith(q) or name.startswith(q):
            starts.append(e)
        elif q in sym or q in name:
            contains.append(e)
    return (starts + contains)[:limit]
