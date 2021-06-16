################## ASSOCIATION RULE LEARNING RECOMMENDER ##################

#### İş Problemi: sepet aşamasındaki kullanıcılara ürün önerisinde bulunmak.

###### Veri Seti Hikayesi ######

# Online Retail II isimli veri seti İngiltere merkezli online bir satış mağazasının 01/12/2009 - 09/12/2011 tarihleri arasındaki satışlarını içeriyor.
# Bu şirketin ürün kataloğunda hediyelik eşyalar yer alıyor. Promosyon ürünleri olarak da düşünülebilir.
# Çoğu müşterisinin toptancı olduğu bilgisi de mevcut.

####### NOT ###########
# Aşağıda 3 farklı kullanıcının sepet bilgileri verilmiştir.
# Bu sepet bilgilerine en uygun ürün önerisini yapınız.
# Not: Ürün önerileri 1 tane ya da 1'den fazla olabilir.
# Önemli not: Karar kurallarını 2010-2011 Germany müşterileri üzerinden türetiniz.
# ▪ Kullanıcı 1 ürün id'si: 21987
# ▪ Kullanıcı 2 ürün id'si: 23235
# ▪ Kullanıcı 3 ürün id'si: 22747

import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 500)
pd.set_option('display.expand_frame_repr', False)
pip install mlxtend
from mlxtend.frequent_patterns import apriori, association_rules

########################### GÖREV 1 ####################################

# Veri Ön İşleme İşlemlerini Gerçekleştiriniz.

# 2010-2011 verilerini seçiniz ve tüm veriyi ön işlemeden geçiriniz.
# Germany seçimi sonraki basamakta yapılacaktır.

df = pd.read_excel("hafta3_python/online_retail_II.xlsx", sheet_name="Year 2010-2011")
df_copy = df.copy()
df.shape

# veri setine bakalım
def check_df(dataframe, head=5):
    print("##################### Shape #####################")
    print(dataframe.shape)
    print("##################### Types #####################")
    print(dataframe.dtypes)
    print("##################### Head #####################")
    print(dataframe.head(head))
    print("##################### Tail #####################")
    print(dataframe.tail(head))
    print("##################### NA #####################")
    print(dataframe.isnull().sum())
    print("##################### Quantiles #####################")
    print(dataframe.quantile([0, 0.05, 0.50, 0.95, 0.99, 1]).T)
check_df(df)


def outlier_thresholds(dataframe, variable):
    quartile1 = dataframe[variable].quantile(0.01)
    quartile3 = dataframe[variable].quantile(0.99)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5 * interquantile_range
    low_limit = quartile1 - 1.5 * interquantile_range
    return low_limit, up_limit
def replace_with_thresholds(dataframe, variable):
    low_limit, up_limit = outlier_thresholds(dataframe, variable)
    dataframe.loc[(dataframe[variable] < low_limit), variable] = low_limit
    dataframe.loc[(dataframe[variable] > up_limit), variable] = up_limit

def retail_data_prep(dataframe):
    dataframe.dropna(inplace=True)
    dataframe = dataframe[~dataframe["Invoice"].str.contains("C", na=False)]
    dataframe = dataframe[dataframe["Quantity"] > 0]
    dataframe = dataframe[dataframe["Price"] > 0]
    replace_with_thresholds(dataframe, "Quantity")
    replace_with_thresholds(dataframe, "Price")
    return dataframe
df = retail_data_prep(df)
df.shape


########################### GÖREV 2 ####################################

##### Germany müşterileri üzderinden birliktelik kuralları üretiniz #####

#### ARL Veri Yapısının Hazırlanması (invoice-product matrix) ####
# invoice-product kesişimleri 1 veya 0 olsun


df_ge = df[df["Country"] == "Germany"]
check_df(df_ge)
df_ge.shape

#hangi üründen kaç tane alındığı
df_ge.groupby(["Invoice", "Description"]).agg({"Quantity":"sum"}).head(20)


df_ge.groupby(["Invoice", "Description"]).agg({"Quantity":"sum"}).unstack().iloc[0:20, 0:20]

#NaN --> 0
df_ge.groupby(["Invoice", "Description"]).agg({"Quantity":"sum"}).unstack().fillna(0).iloc[0:20, 0:20]


df_ge.groupby(["Invoice", "Description"]).agg({"Quantity":"sum"}).unstack().fillna(0).applymap(lambda x: 1 if x > 0 else 0).iloc[0:20, 0:20]

# fonksiyonlaştırma
def create_invoice_product_df(dataframe, id=False):
    if id:
        return dataframe.groupby(['Invoice', "StockCode"])['Quantity'].sum().unstack().fillna(0). \
            applymap(lambda x: 1 if x > 0 else 0)
    else:
        return dataframe.groupby(['Invoice', 'Description'])['Quantity'].sum().unstack().fillna(0). \
            applymap(lambda x: 1 if x > 0 else 0)

# fonksiyonla yapılması:
# id=True stock code'larını getirir, id=False descriptionlar'ı getirir. (aynı şey)
ge_inv_pro_df = create_invoice_product_df(df_ge)
ge_inv_pro_df = create_invoice_product_df(df_ge, id=True)
ge_inv_pro_df.head()

# stock code'un hangi ürün olduğunu görmek
def check_id(dataframe, stock_code):
    product_name = dataframe[dataframe["StockCode"] == stock_code][["Description"]].values[0].tolist()
    print(product_name)

###### Birliktelik Kuralları #######

#apriori ile sadece support'u hesapla
frequent_itemsets = apriori(ge_inv_pro_df, min_support=0.01, use_colnames=True)
frequent_itemsets.sort_values(by="support", ascending=False).head()

#association_rules ile diğer tüm metrikleri hesapla
rules = association_rules(frequent_itemsets, metric="support", min_threshold=0.01)
rules.sort_values(by="support", ascending=False).head()

#antecendents: önceki ürün.
#consequents: sonraki ürün.
#antecendents support: önceki ürünün tek başına olasılığı.
#consequent support: sonraki ürünün tek başına olasılığı.
#support: iki ürünün birlikte görülme olasılığı.
#confidence: birisi alındığında diğerinin alınma olasılığı.
#lift: biri alındığında diğerinin alınma olasılığının ne kadar kat arttığı.

rules.sort_values(by="lift", ascending=False).head(100)
rules.sort_values(by="confidence", ascending=False).head(100)


########################### GÖREV 3 ####################################

# ID'leri verilen ürünlerin isimleri nelerdir?
# Kullanıcı 1 ürün id'si: 21987
# Kullanıcı 2 ürün id'si: 23235
# Kullanıcı 3 ürün id'si: 22747

check_id(df_ge, 21987)
check_id(df_ge, 23235)
check_id(df_ge, 22747)

########################### GÖREV 4 ####################################

# Sepetteki kullanıcılar için ürün önerisi yapınız.

# Kullanıcı 1 örnek ürün id'si: 21987

product_id = 21987
check_id(df, product_id)

sorted_rules = rules.sort_values("lift", ascending=False)

recommendation_list = []

for i, product in enumerate(sorted_rules["antecedents"]):
    for j in list(product):
        if j == product_id:
            recommendation_list.append(list(sorted_rules.iloc[i]["consequents"])[0])

# 2 tane ürün önerisi geliyor
recommendation_list[0:2]


def arl_recommender(rules_df, product_id, rec_count=1):
    sorted_rules = rules_df.sort_values("lift", ascending=False)
    recommendation_list = []
    for i, product in enumerate(sorted_rules["antecedents"]):
        for j in list(product):
            if j == product_id:
                recommendation_list.append(list(sorted_rules.iloc[i]["consequents"])[0])
    return recommendation_list[0:rec_count]

arl_recommender(rules, 21987, 1)
#21086

arl_recommender(rules, 23235, 1)
#23244

arl_recommender(rules, 22747, 1)
#22745

########################### GÖREV 5 ####################################

# Ürünlerin isimleri nelerdir?

check_id(df,21989)
# PACK OF 20 SKULL PAPER NAPKINS

check_id(df,23243)
# SET OF TEA COFFEE SUGAR TINS PANTRY

check_id(df,22745)
# POPPY'S PLAYHOUSE BEDROOM